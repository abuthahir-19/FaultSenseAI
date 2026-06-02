import re
from typing import Dict, Any
from loguru import logger

TELECOM_KEYWORDS = {
    "5g", "4g", "lte", "ran", "bts", "enodeb", "gnodeb", "tower", "fiber",
    "latency", "outage", "alarm", "fault", "incident", "network", "signal",
    "coverage", "call drop", "handover", "interference", "synchronization",
    "ericsson", "nokia", "huawei", "cisco", "juniper", "bandwidth", "packet",
    "router", "switch", "core", "backhaul", "radio", "frequency", "spectrum",
    "congestion", "throughput", "jitter", "ping", "mtu", "vlan", "mpls",
    "configuration", "upgrade", "downtime", "sla", "kpi", "vswr", "rssi",
    "disconnection", "timeout", "reset", "crash", "degradation", "failure",
    "connectivity", "drop", "ping", "link", "port", "interface", "route",
}

INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"you are now",
    r"forget your",
    r"pretend you",
    r"act as(?!\s+a\s+telecom)",
    r"<script",
    r"'; drop table",
    r"system prompt",
    r"jailbreak",
    r"bypass.*filter",
]


def validate_query(query: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"valid": True, "warnings": [], "error": None}

    if not query or not query.strip():
        result["valid"] = False
        result["error"] = "Query cannot be empty."
        return result

    if len(query.strip()) < 10:
        result["valid"] = False
        result["error"] = "Query too short. Please describe the network issue in more detail (min 10 chars)."
        return result

    if len(query) > 2000:
        result["valid"] = False
        result["error"] = "Query too long. Please limit to 2000 characters."
        return result

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            result["valid"] = False
            result["error"] = "Query contains disallowed content."
            logger.warning(f"Injection pattern detected in query: {pattern}")
            return result

    query_lower = query.lower()
    has_telecom_keyword = any(kw in query_lower for kw in TELECOM_KEYWORDS)
    if not has_telecom_keyword:
        result["warnings"].append(
            "No telecom-specific keywords detected. Results may be less accurate. "
            "Consider mentioning network technology (5G/4G/Fiber), region, or device type."
        )

    logger.debug(f"Query validated: valid={result['valid']}, warnings={len(result['warnings'])}")
    return result
