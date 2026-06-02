"""
Evaluation module using DeepEval metrics.

Three evaluation dimensions (RAGAS-aligned):
  1. Faithfulness         — root cause & recommendations grounded in retrieved incidents
  2. Answer Relevancy     — root cause directly addresses the query
  3. Contextual Relevancy — fraction of retrieved incidents that are truly relevant

Uses a custom DeepEvalBaseLLM subclass so all LLM calls go through our configured
OpenAI client (supports custom base_url + SSL bypass for the corporate proxy gateway).

Also provides an LLM cross-encoder reranker that rescores retrieved incidents
and blends judge_score with rrf_score for improved ranking.
"""

import json
from typing import List, Dict, Any, Optional, Union
from loguru import logger

from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualRelevancyMetric,
)

from backend.app.config import get_settings, get_openai_client


# ── Custom DeepEval LLM wrapper ───────────────────────────────────────────────

class _TelecomEvalModel(DeepEvalBaseLLM):
    """
    Routes DeepEval metric LLM calls through our OpenAI client.
    This ensures the custom base_url and SSL-bypass httpx client are used
    instead of DeepEval's default OpenAI instantiation.
    """

    def __init__(self):
        self._client = get_openai_client()
        self._model_name = get_settings().OPENAI_MODEL

    def load_model(self):
        return self._client

    def generate(self, prompt: str, schema=None) -> Union[str, Any]:
        if schema is not None:
            resp = self._client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=512,
            )
            raw = resp.choices[0].message.content or "{}"
            try:
                return schema(**json.loads(raw))
            except Exception:
                return raw
        resp = self._client.chat.completions.create(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=512,
        )
        return resp.choices[0].message.content or ""

    async def a_generate(self, prompt: str, schema=None) -> Union[str, Any]:
        return self.generate(prompt, schema=schema)

    def get_model_name(self) -> str:
        return self._model_name


# ── LLM Reranker ──────────────────────────────────────────────────────────────

RERANK_SYSTEM = (
    "You are a telecom network fault retrieval expert. "
    "Score how relevant the incident is to the user query on a scale 0.0-1.0. "
    'Return ONLY valid JSON: {"score": <float 0.0-1.0>, "reason": "<one sentence>"}. '
    "Scoring guide: "
    "1.0=exact technology+region+symptom match, "
    "0.7=same technology+similar symptoms, "
    "0.5=related technology or partial symptom match, "
    "0.2=tangentially related, "
    "0.0=completely unrelated."
)


def rerank_incidents(
    query: str,
    incidents: List[Dict[str, Any]],
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    """
    LLM cross-encoder reranker.

    For each retrieved incident, calls the LLM to score relevance (0-1).
    Blends:  combined_score = 0.6 * judge_score + 0.4 * normalised_rrf_score
    Returns top_k incidents sorted by combined_score descending.
    Each incident dict gets three new fields: judge_score, judge_reason, combined_score.
    """
    if not incidents:
        return []

    settings = get_settings()
    client = get_openai_client()
    scored = []

    for inc in incidents:
        snippet = (
            f"Technology: {inc.get('technology_type', '?')} | "
            f"Region: {inc.get('network_region', '?')} | "
            f"Vendor: {inc.get('device_vendor', '?')} | "
            f"Severity: {inc.get('severity', '?')}\n"
            f"Description: {str(inc.get('incident_description', ''))[:300]}"
        )
        try:
            resp = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": RERANK_SYSTEM},
                    {"role": "user", "content": f"Query: {query}\n\nIncident:\n{snippet}"},
                ],
                max_tokens=80,
                response_format={"type": "json_object"},
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            judge_score = float(data.get("score", 0.5))
            judge_reason = str(data.get("reason", ""))
        except Exception as e:
            logger.debug(f"Reranker error for {inc.get('alarm_id')}: {e}")
            judge_score, judge_reason = 0.5, ""

        rrf = float(inc.get("rrf_score", 0.0))
        normalised_rrf = min(rrf * 200, 1.0)
        combined = round(0.6 * judge_score + 0.4 * normalised_rrf, 4)

        inc = inc.copy()
        inc["judge_score"] = round(judge_score, 3)
        inc["judge_reason"] = judge_reason
        inc["combined_score"] = combined
        scored.append(inc)

    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    logger.info(f"Reranked {len(scored)} incidents for: '{query[:60]}'")
    return scored[:top_k]


# ── DeepEval evaluation ───────────────────────────────────────────────────────

def evaluate_analysis(
    query: str,
    retrieved_incidents: List[Dict[str, Any]],
    root_cause: str,
    recommendations: List[str],
) -> Dict[str, Any]:
    """
    Evaluates RAG output quality using DeepEval metrics.

    Metrics:
      • FaithfulnessMetric      — is the answer grounded in the retrieved context?
      • AnswerRelevancyMetric   — does the answer address the query?
      • ContextualRelevancyMetric — are retrieved incidents relevant to the query?

    Weighted overall score (RAGAS-aligned):
      overall = 0.40 * faithfulness + 0.35 * answer_relevance + 0.25 * context_relevancy
    """
    model = _TelecomEvalModel()

    # Build the "actual output" shown to DeepEval as the generated answer
    actual_output = (
        f"Root Cause Analysis:\n{root_cause}\n\n"
        f"Recommendations:\n" + "\n".join(f"{i+1}. {r}" for i, r in enumerate(recommendations[:10]))
    )

    # Build retrieval context strings (one per incident)
    retrieval_context = [
        (
            f"[{inc.get('alarm_id', '?')}] "
            f"{inc.get('technology_type', '?')} | "
            f"{inc.get('network_region', '?')} | "
            f"{inc.get('severity', '?')} | "
            f"{inc.get('device_vendor', '?')} -- "
            f"{str(inc.get('incident_description', ''))[:200]} "
            f"Resolution: {str(inc.get('resolution_notes', ''))[:100]}"
        )
        for inc in retrieved_incidents[:8]
    ]

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        retrieval_context=retrieval_context,
    )

    results: Dict[str, Any] = {
        "query": query,
        "faithfulness": {},
        "answer_relevance": {},
        "context_precision": {},
        "overall_score": 0.0,
        "evaluation_summary": "",
    }

    f_score, rv_score, p_score = 0.0, 0.0, 0.0

    # 1. Faithfulness
    try:
        faithfulness = FaithfulnessMetric(model=model, threshold=0.5, verbose_mode=False)
        faithfulness.measure(test_case)
        f_score = faithfulness.score or 0.0
        results["faithfulness"] = {
            "faithfulness_score": round(f_score, 3),
            "grounding_assessment": faithfulness.reason or "",
            "issues": [],
        }
        logger.info(f"DeepEval Faithfulness: {f_score:.3f} — {faithfulness.reason}")
    except Exception as e:
        logger.warning(f"FaithfulnessMetric failed: {e}")
        results["faithfulness"] = {"faithfulness_score": 0.0, "grounding_assessment": str(e), "issues": []}

    # 2. Answer Relevancy
    try:
        relevancy = AnswerRelevancyMetric(model=model, threshold=0.5, verbose_mode=False)
        relevancy.measure(test_case)
        rv_score = relevancy.score or 0.0
        results["answer_relevance"] = {
            "relevance_score": round(rv_score, 3),
            "relevance_assessment": relevancy.reason or "",
            "missing_aspects": [],
        }
        logger.info(f"DeepEval Answer Relevancy: {rv_score:.3f} — {relevancy.reason}")
    except Exception as e:
        logger.warning(f"AnswerRelevancyMetric failed: {e}")
        results["answer_relevance"] = {"relevance_score": 0.0, "relevance_assessment": str(e), "missing_aspects": []}

    # 3. Contextual Relevancy
    try:
        ctx_relevancy = ContextualRelevancyMetric(model=model, threshold=0.5, verbose_mode=False)
        ctx_relevancy.measure(test_case)
        p_score = ctx_relevancy.score or 0.0
        results["context_precision"] = {
            "context_precision_score": round(p_score, 3),
            "precision_assessment": ctx_relevancy.reason or "",
        }
        logger.info(f"DeepEval Contextual Relevancy: {p_score:.3f} — {ctx_relevancy.reason}")
    except Exception as e:
        logger.warning(f"ContextualRelevancyMetric failed: {e}")
        results["context_precision"] = {"context_precision_score": 0.0, "precision_assessment": str(e)}

    overall = round(f_score * 0.40 + rv_score * 0.35 + p_score * 0.25, 3)
    results["overall_score"] = overall
    results["evaluation_summary"] = (
        f"Overall: {overall:.0%} | "
        f"Faithfulness: {f_score:.0%} | "
        f"Answer Relevance: {rv_score:.0%} | "
        f"Contextual Relevancy: {p_score:.0%}"
    )

    logger.info(f"DeepEval evaluation complete — {results['evaluation_summary']}")
    return results
