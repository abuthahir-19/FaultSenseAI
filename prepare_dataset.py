"""
prepare_dataset.py
==================
Downloads and transforms publicly available telecom fault datasets into the
10-field incident schema required by TelecomNetworkFaultIntel.

Primary sources (auto-downloaded, no login required):
  1. greenwich157/5G_Faults_Full     — HuggingFace, Apache 2.0
     1,993 rows of real 5G fault scenarios + detailed resolution guidance

  2. greenwich157/telco-5G-data-faults — HuggingFace, Apache 2.0
     705 rows with SYMPTOMS / CAUSES / ACTIONS structure

Both datasets provide authentic natural-language fault descriptions and
resolution notes. Structured metadata (alarm_id, severity, vendor, region,
technology_type, outage_duration, timestamp) is derived from the text content
via keyword extraction and rule-based classification.

Usage
-----
    python prepare_dataset.py

Output: data/telecom_incidents.csv  (ready for: python ingest_data.py)

If you already have a raw CSV from Kaggle / elsewhere:
    python prepare_dataset.py --input data/raw/your_file.csv
"""

import argparse
import csv
import os
import random
import re
import sys
from datetime import datetime, timedelta
from typing import Optional

random.seed(42)

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "telecom_incidents.csv")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

# ── Structured metadata pools ──────────────────────────────────────────────────

VENDORS  = ["Ericsson", "Nokia", "Huawei", "Cisco", "Juniper"]
VENDOR_W = [0.25, 0.22, 0.28, 0.15, 0.10]

REGIONS  = [
    "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
    "Kolkata", "Pune", "Ahmedabad", "Singapore", "London",
    "Dubai", "New York", "Tokyo", "Frankfurt", "Sydney",
    "Toronto", "Jakarta", "Nairobi", "São Paulo", "Paris",
]

TECHNOLOGIES = ["5G-NR", "4G-LTE", "3G-UMTS", "Fiber-Optic",
                "MPLS-Core", "RAN", "IP-Core", "Microwave-Backhaul", "Cloud-RAN"]

SERVICE_IMPACTS = [
    "Voice calls affected", "Data sessions degraded", "SMS delivery delayed",
    "Emergency services impacted", "Enterprise VPN disrupted",
    "IoT connectivity lost", "Mobile broadband throughput reduced",
    "Roaming services unavailable", "Video streaming interrupted",
    "Fixed broadband users affected", "Cloud-hosted applications unreachable",
    "Inter-site backhaul degraded", "Financial transaction services disrupted",
    "Public safety network degraded", "Wholesale transit impacted",
]

OUTAGE_RANGES = {
    "CRITICAL": (60, 480),
    "HIGH":     (20, 180),
    "MEDIUM":   (5,  90),
    "LOW":      (1,  30),
}

# ── Keyword-based text classifiers ────────────────────────────────────────────

SEVERITY_CRITICAL_KW = [
    "complete outage", "total loss", "all users", "mass", "black hole",
    "emergency", "down", "unavailable", "failed", "crash", "critical",
    "100%", "severe", "total failure", "complete failure", "catastrophic",
]
SEVERITY_HIGH_KW = [
    "significant", "major", "high", "multiple", "widespread", "substantial",
    "severe degradation", "large scale", "escalated", "urgent", "dropped",
]
SEVERITY_LOW_KW = [
    "minor", "slight", "intermittent", "occasional", "partial", "low",
    "degraded", "reduced", "marginal", "negligible",
]

TECH_KEYWORDS = {
    "5G-NR":             ["5g", "nr", "gnodeb", "gnb", "mmwave", "n78", "n41",
                           "5g nr", "standalone", "nsa", "5g sa", "5g nsa", "amf", "upf",
                           "smf", "nrf", "ausf", "pcf", "udm", "nssf", "n2", "n3",
                           "pdu session", "urllc", "embb", "network slice"],
    "4G-LTE":            ["lte", "4g", "enodeb", "enb", "epc", "mme", "s-gw",
                           "p-gw", "volte", "carrier aggregation", "csfb", "4g lte",
                           "e-utran", "eps bearer", "qci", "s1", "x2"],
    "3G-UMTS":           ["3g", "umts", "wcdma", "nodeb", "rnc", "hspa", "hsdpa",
                           "hsupa", "iub", "iur", "3g umts", "r99"],
    "Cloud-RAN":         ["cloud-ran", "c-ran", "vran", "o-ran", "oran", "vdu",
                           "vcu", "kubernetes", "container", "docker", "openran",
                           "o-du", "o-cu", "near-rt ric", "xapp", "smf", "a1"],
    "RAN":               ["ran", "rru", "bbu", "cpri", "ecpri", "radio access",
                           "base station", "bts", "cell site", "sector"],
    "Fiber-Optic":       ["fiber", "fibre", "dwdm", "olt", "onu", "optical",
                           "otdr", "roadm", "edfa", "osnr", "wdm", "splice", "ber"],
    "MPLS-Core":         ["mpls", "bgp", "ospf", "ldp", "rsvp-te", "vpn", "vrf",
                           "pe router", "lsp", "l3vpn", "l2vpn", "pseudowire"],
    "IP-Core":           ["ip", "router", "routing", "bgp", "ospf", "isis",
                           "core network", "backbone", "transit", "peering"],
    "Microwave-Backhaul":["microwave", "backhaul", "odu", "idu", "mw link",
                           "ptp", "ptmp", "e-band", "rain fade", "acm"],
}

VENDOR_KEYWORDS = {
    "Ericsson": ["ericsson", "erbs", "ericsson rbs", "aiu", "diu"],
    "Nokia":    ["nokia", "nsn", "nokia siemens", "airscale", "nokia bell"],
    "Huawei":   ["huawei", "bts3900", "bts5900", "rru3908", "huawei"],
    "Cisco":    ["cisco", "ios", "ios-xe", "ios-xr", "nx-os", "asr", "crs"],
    "Juniper":  ["juniper", "junos", "mx series", "srx", "qfx"],
}


def weighted_choice(items, weights):
    total = sum(weights)
    r = random.random() * total
    c = 0
    for item, w in zip(items, weights):
        c += w
        if r < c:
            return item
    return items[-1]


def extract_technology(text: str) -> str:
    text_l = text.lower()
    for tech, keywords in TECH_KEYWORDS.items():
        for kw in keywords:
            if kw in text_l:
                return tech
    return random.choice(TECHNOLOGIES)


def extract_vendor(text: str) -> str:
    text_l = text.lower()
    for vendor, keywords in VENDOR_KEYWORDS.items():
        for kw in keywords:
            if kw in text_l:
                return vendor
    return weighted_choice(VENDORS, VENDOR_W)


def classify_severity(text: str) -> str:
    text_l = text.lower()
    if any(kw in text_l for kw in SEVERITY_CRITICAL_KW):
        return "CRITICAL"
    if any(kw in text_l for kw in SEVERITY_HIGH_KW):
        return "HIGH"
    if any(kw in text_l for kw in SEVERITY_LOW_KW):
        return "LOW"
    return "MEDIUM"


def random_timestamp() -> str:
    start = datetime(2024, 1, 1)
    end   = datetime(2026, 6, 1)
    delta = (end - start).total_seconds()
    dt    = start + timedelta(seconds=random.randint(0, int(delta)))
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def make_alarm_id(ts: str, seq: int) -> str:
    date_part = ts[:10].replace("-", "")
    return f"ALM-{date_part}-{seq:04d}"


def pick_service_impact(text: str) -> str:
    text_l = text.lower()
    if any(w in text_l for w in ["voice", "call", "voip", "volte"]):
        return "Voice calls affected"
    if any(w in text_l for w in ["sms", "messaging", "text"]):
        return "SMS delivery delayed"
    if any(w in text_l for w in ["iot", "internet of things", "sensor"]):
        return "IoT connectivity lost"
    if any(w in text_l for w in ["enterprise", "vpn", "corporate"]):
        return "Enterprise VPN disrupted"
    if any(w in text_l for w in ["emergency", "public safety", "first responder"]):
        return "Emergency services impacted"
    if any(w in text_l for w in ["video", "stream", "youtube"]):
        return "Video streaming interrupted"
    if any(w in text_l for w in ["data", "broadband", "internet", "throughput"]):
        return "Mobile broadband throughput reduced"
    return random.choice(SERVICE_IMPACTS)


def build_row(seq: int, description: str, resolution: str,
              region: Optional[str] = None,
              vendor: Optional[str] = None,
              technology: Optional[str] = None,
              severity: Optional[str] = None,
              ts: Optional[str] = None) -> dict:
    combined = description + " " + resolution
    ts       = ts or random_timestamp()
    sev      = severity or classify_severity(combined)
    lo, hi   = OUTAGE_RANGES[sev]
    return {
        "alarm_id":             make_alarm_id(ts, seq),
        "incident_description": description.strip(),
        "network_region":       region or random.choice(REGIONS),
        "technology_type":      technology or extract_technology(combined),
        "severity":             sev,
        "outage_duration":      random.randint(lo, hi),
        "device_vendor":        vendor or extract_vendor(combined),
        "resolution_notes":     resolution.strip(),
        "timestamp":            ts,
        "service_impact":       pick_service_impact(combined),
    }


# ── HuggingFace download helper ───────────────────────────────────────────────

def _hf_load_dataset(repo_id: str, split: str = "train") -> list[dict]:
    """
    Load a HuggingFace dataset via:
      1. `datasets` library (preferred)
      2. Direct parquet HTTP download (fallback)
    Handles both list-of-strings and list-of-dicts HF API responses.
    """
    import pandas as pd, requests

    # Strategy 1: datasets library
    try:
        from datasets import load_dataset
        ds = load_dataset(repo_id, split=split)
        df = ds.to_pandas()
        print(f"  [OK] datasets lib: {len(df)} rows, cols: {list(df.columns)}")
        return df.to_dict(orient="records")
    except Exception as e1:
        print(f"  [datasets lib unavailable: {e1}] -- trying direct parquet...")

    # Strategy 2: HuggingFace parquet API + direct download
    try:
        api_url = f"https://huggingface.co/api/datasets/{repo_id}/parquet/default/{split}"
        resp = requests.get(api_url, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"HF API {resp.status_code}")
        data = resp.json()

        # API may return list of strings (URLs) or list of dicts with 'url' key
        if data and isinstance(data[0], str):
            parquet_urls = data
        elif data and isinstance(data[0], dict):
            parquet_urls = [f.get("url") or f.get("filename") for f in data if f.get("url") or f.get("filename")]
        else:
            raise RuntimeError(f"Unexpected API response type: {type(data[0]) if data else 'empty'}")

        frames = [pd.read_parquet(u) for u in parquet_urls if u]
        df = pd.concat(frames, ignore_index=True)
        print(f"  [OK] direct parquet: {len(df)} rows, cols: {list(df.columns)}")
        return df.to_dict(orient="records")
    except Exception as e2:
        raise RuntimeError(f"All strategies failed. Last error: {e2}") from e2


# ── Source 1: HuggingFace greenwich157/5G_Faults_Full ─────────────────────────

def load_hf_5g_faults_full() -> list[dict]:
    """
    Dataset: greenwich157/5G_Faults_Full (Apache 2.0, 1,993 rows)
    Fields: instruction, input (fault scenario), output (resolution)
    """
    print("  Downloading greenwich157/5G_Faults_Full from HuggingFace...")
    try:
        rows = _hf_load_dataset("greenwich157/5G_Faults_Full")
        print(f"  Loaded {len(rows)} rows.")
        return rows
    except Exception as e:
        print(f"  [FAIL] {e}")
        return []


def transform_5g_faults_full(raw_rows: list[dict], start_seq: int) -> list[dict]:
    rows, seq = [], start_seq
    for r in raw_rows:
        desc = str(r.get("input") or r.get("instruction") or "").strip()
        res  = str(r.get("output") or "").strip()
        if not desc or not res or len(desc) < 30:
            continue
        rows.append(build_row(seq, desc, res))
        seq += 1
    print(f"  Transformed {len(rows)} incidents from 5G_Faults_Full")
    return rows


# ── Source 2: HuggingFace greenwich157/telco-5G-data-faults ──────────────────

def load_hf_telco_faults() -> list[dict]:
    """
    Dataset: greenwich157/telco-5G-data-faults (Apache 2.0, 705 rows)
    Each row is a text block with [SYSTEM], [SYMPTOMS], [CAUSES], [ACTIONS] sections.
    """
    print("  Downloading greenwich157/telco-5G-data-faults from HuggingFace...")
    try:
        rows = _hf_load_dataset("greenwich157/telco-5G-data-faults")
        print(f"  Loaded {len(rows)} rows.")
        return rows
    except Exception as e:
        print(f"  [FAIL] {e}")
        return []


_SECTION_RE = re.compile(
    r"\[SYMPTOMS\](.*?)(?=\[CAUSES\]|\[ACTIONS\]|\Z)"
    r"|\[CAUSES\](.*?)(?=\[ACTIONS\]|\Z)"
    r"|\[ACTIONS\](.*?)(?=\[SYMPTOMS\]|\[CAUSES\]|\Z)",
    re.DOTALL | re.IGNORECASE,
)


def _parse_sections(text: str) -> tuple[str, str, str]:
    symptoms, causes, actions = "", "", ""
    for m in _SECTION_RE.finditer(text):
        if m.group(1) is not None:
            symptoms = m.group(1).strip()
        elif m.group(2) is not None:
            causes = m.group(2).strip()
        elif m.group(3) is not None:
            actions = m.group(3).strip()
    return symptoms, causes, actions


def transform_telco_faults(raw_rows: list[dict], start_seq: int) -> list[dict]:
    rows, seq = [], start_seq
    for r in raw_rows:
        text = str(r.get("text") or "").strip()
        if not text:
            continue
        symptoms, causes, actions = _parse_sections(text)
        # Build description from symptoms + causes; resolution from actions
        if symptoms and causes:
            desc = f"{symptoms} Root cause: {causes}"
        elif symptoms:
            desc = symptoms
        elif causes:
            desc = causes
        else:
            desc = text[:300]
        res = actions or "Issue resolved following standard troubleshooting procedure."
        if len(desc) < 20:
            continue
        rows.append(build_row(seq, desc, res))
        seq += 1
    print(f"  [OK]  Transformed {len(rows)} incidents from telco-5G-data-faults")
    return rows


# ── Source 3: GoMask.ai Network Outage Incident Logs (sample) ─────────────────

def load_gomask_outage_sample() -> list[dict]:
    """
    Dataset: GoMask.ai Network Outage Incident Logs (public sample, no login)
    Falls back gracefully if the endpoint is unavailable.
    """
    print("  Fetching GoMask.ai Network Outage Incident Logs sample...")
    try:
        import requests
        # GoMask public sample endpoint (JSON preview)
        url = "https://gomask.ai/api/datasets/network-outage-incident-logs/sample"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")
        data = resp.json()
        rows = data if isinstance(data, list) else data.get("data", [])
        print(f"  [OK]  Loaded {len(rows)} rows from GoMask.ai sample")
        return rows
    except Exception as e:
        print(f"  [SKIP]  GoMask.ai sample unavailable ({e}) — skipping")
        return []


def transform_gomask(raw_rows: list[dict], start_seq: int) -> list[dict]:
    rows, seq = [], start_seq
    for r in raw_rows:
        # GoMask columns: Incident ID, Provider Name, Incident Start Time, Duration Minutes,
        # Affected Region, Affected Services, Severity Level, Root Cause, Resolution Summary
        desc = str(r.get("Root Cause") or r.get("root_cause") or "").strip()
        res  = str(r.get("Resolution Summary") or r.get("resolution_summary") or "").strip()
        if not desc or len(desc) < 15:
            continue

        region  = str(r.get("Affected Region") or r.get("affected_region") or "")
        sev_raw = str(r.get("Severity Level") or r.get("severity_level") or "")
        dur_raw = r.get("Duration Minutes") or r.get("duration_minutes")
        ts_raw  = str(r.get("Incident Start Time") or r.get("incident_start_time") or "")
        svc_raw = str(r.get("Affected Services") or r.get("affected_services") or "")

        sev_map = {"critical": "CRITICAL", "high": "HIGH",
                   "medium": "MEDIUM", "low": "LOW", "moderate": "MEDIUM"}
        sev = sev_map.get(sev_raw.lower(), classify_severity(desc))

        ts = None
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                ts = datetime.strptime(str(ts_raw)[:19], fmt).strftime("%Y-%m-%d %H:%M:%S")
                break
            except ValueError:
                continue

        row = build_row(seq, desc, res,
                        region=region or None,
                        severity=sev,
                        ts=ts)
        if dur_raw:
            try:
                row["outage_duration"] = int(float(dur_raw))
            except (ValueError, TypeError):
                pass
        if svc_raw:
            row["service_impact"] = svc_raw[:100]
        rows.append(row)
        seq += 1
    print(f"  [OK]  Transformed {len(rows)} incidents from GoMask.ai")
    return rows


# ── Source 4: Telstra Network Disruption dataset ──────────────────────────────
#
# Files (all share a common `id` key, stored as data/<name>.csv/<name>.csv):
#   train.csv        — id, location, fault_severity  (7381 rows, labelled)
#   event_type.csv   — id, event_type                (31170 rows, 1-11 per id, 53 types)
#   log_feature.csv  — id, log_feature, volume        (58671 rows, up to 386 feature types)
#   resource_type.csv— id, resource_type             (21076 rows, 10 types → technology)
#   severity_type.csv— id, severity_type             (18552 rows, 5 types  → vendor)
#
# Mapping strategy:
#   event_type  (53 codes)    → 9 fault categories  → NL description + resolution
#   resource_type (10 codes)  → technology_type
#   severity_type (5 codes)   → device_vendor
#   fault_severity (0/1/2)    → LOW-MEDIUM / HIGH / CRITICAL
#   location (929 anon codes) → one of 20 real city names (stable hash)


_TELSTRA_REGIONS = [
    "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
    "Auckland", "Singapore", "Mumbai", "Jakarta", "Kuala Lumpur",
    "Tokyo", "Seoul", "London", "Frankfurt", "Dubai",
    "Toronto", "New York", "Chicago", "São Paulo", "Nairobi",
]

_RESOURCE_TO_TECH = {
    "resource_type 1":  "5G-NR",
    "resource_type 2":  "4G-LTE",
    "resource_type 3":  "3G-UMTS",
    "resource_type 4":  "Fiber-Optic",
    "resource_type 5":  "MPLS-Core",
    "resource_type 6":  "RAN",
    "resource_type 7":  "IP-Core",
    "resource_type 8":  "Microwave-Backhaul",
    "resource_type 9":  "Cloud-RAN",
    "resource_type 10": "Fiber-Optic",
}

_SEVERITY_TO_VENDOR = {
    "severity_type 1": "Ericsson",
    "severity_type 2": "Nokia",
    "severity_type 3": "Huawei",
    "severity_type 4": "Cisco",
    "severity_type 5": "Juniper",
}

_FAULT_TO_SEVERITY = {"0": ["LOW", "MEDIUM"], "1": ["HIGH"], "2": ["CRITICAL"]}

# Technology-specific node / protocol / metric vocabulary
_TECH_VOCAB = {
    "5G-NR":             dict(node="gNodeB",           iface="NG/N2 interface",    metric="SINR/RSRP",          proto="NGAP",        session="PDU session",      ctrl="AMF"),
    "4G-LTE":            dict(node="eNodeB",           iface="S1 interface",       metric="CQI/RSRQ",           proto="S1AP",        session="EPS bearer",       ctrl="MME"),
    "3G-UMTS":           dict(node="NodeB/RNC",        iface="Iub interface",      metric="Ec/No CPICH",        proto="NBAP/RANAP",  session="RAB",              ctrl="SGSN"),
    "Fiber-Optic":       dict(node="DWDM transponder", iface="optical span",       metric="OSNR/pre-FEC BER",   proto="OAM/OTDR",    session="wavelength ch.",   ctrl="ROADM"),
    "MPLS-Core":         dict(node="PE/P router",      iface="MPLS backbone link", metric="jitter/packet loss", proto="BGP/LDP",     session="LSP tunnel",       ctrl="Route Reflector"),
    "RAN":               dict(node="BBU/RRU",          iface="CPRI/eCPRI link",    metric="VSWR/RSSI",          proto="OAM",         session="radio bearer",     ctrl="RAN controller"),
    "IP-Core":           dict(node="core router",      iface="IP backbone link",   metric="latency/loss",       proto="BGP/OSPF",    session="IP flow",          ctrl="Route Reflector"),
    "Microwave-Backhaul":dict(node="microwave ODU",    iface="MW radio link",      metric="RSL/ACM modulation", proto="Ethernet/E1", session="traffic channel",  ctrl="NMS"),
    "Cloud-RAN":         dict(node="vCU/vDU pod",      iface="fronthaul F1 link",  metric="CPU/memory usage",   proto="eCPRI",       session="PDU session",      ctrl="Kubernetes/SMO"),
}

def _event_to_category(n: int) -> str:
    """Map event_type number (1-54) to one of 9 fault categories."""
    if n <= 6:   return "signal_degradation"
    if n <= 12:  return "interface_failure"
    if n <= 18:  return "hardware_fault"
    if n <= 24:  return "software_config_error"
    if n <= 30:  return "capacity_congestion"
    if n <= 36:  return "sync_timing_failure"
    if n <= 42:  return "backhaul_transport"
    if n <= 48:  return "core_network_failure"
    return "power_environmental"

_TELSTRA_DESC = {
    "signal_degradation": [
        "{vendor} {node} at site {site} in {region} reported severe signal quality degradation. {metric} levels dropped below threshold, causing coverage reduction and service disruption for connected subscribers.",
        "Coverage anomaly detected on {vendor} {node} serving {region}. Measured {metric} fell outside operational limits, resulting in increased error rates and reduced throughput on active {session}s.",
        "Signal degradation alarm on {vendor} {node} at {site}. {metric} degradation observed across multiple sectors in {region}, impacting call quality and data session stability.",
    ],
    "interface_failure": [
        "{vendor} {node} at {site} reported {iface} failure. Loss of {proto} signaling disrupted active {session}s in {region}, triggering automatic fallback procedures.",
        "{iface} connectivity lost between {vendor} {node} and {ctrl} at {site}. {proto} session termination caused service interruption for subscribers in {region}.",
        "Critical {iface} outage on {vendor} {node} at {site}. Accumulated {proto} signaling failures caused {session} drops for affected subscribers in {region}.",
    ],
    "hardware_fault": [
        "{vendor} {node} hardware fault detected at {site}. Component failure degraded {metric} and caused partial service outage affecting {session}s in {region}.",
        "Hardware alarm on {vendor} {node} at {site}. Physical layer failure impacted {iface} integrity, causing reduced capacity and {metric} degradation in {region}.",
        "Critical hardware failure on {vendor} {node} at {site}. Equipment malfunction interrupted {iface} and disrupted {session}s for subscribers in {region}.",
    ],
    "software_config_error": [
        "{vendor} {node} at {site} experienced software exception causing {proto} process failure. Configuration inconsistency resulted in {session} management errors in {region}.",
        "Software fault on {vendor} {node} in {region}. Process crash in {proto} stack caused unexpected {session} drops and {iface} instability at {site}.",
        "{vendor} {node} configuration error at {site} triggered {proto} signaling failures, causing {session} establishment failures for subscribers in {region}.",
    ],
    "capacity_congestion": [
        "{vendor} {node} at {site} experiencing capacity overload. {metric} utilization exceeded threshold, causing {session} admission failures and throughput degradation in {region}.",
        "Congestion alarm on {vendor} {node} serving {region}. Peak traffic load exceeded planned capacity, resulting in {session} rejection and degraded {metric} at {site}.",
        "{vendor} {node} capacity limit reached at {site}. Resource exhaustion on {iface} caused {proto} scheduler congestion, impacting users in {region}.",
    ],
    "sync_timing_failure": [
        "{vendor} {node} at {site} lost synchronization reference. Timing failure degraded {metric} and caused {iface} instability, disrupting services in {region}.",
        "Synchronization alarm on {vendor} {node} serving {region}. Clock reference failure at {site} caused {proto} timing violations and {session} instability.",
        "{vendor} {node} timing fault at {site}. Loss of synchronization degraded {iface} performance and caused {metric} threshold violations in {region}.",
    ],
    "backhaul_transport": [
        "{vendor} {node} at {site} reported backhaul degradation. Transport fault elevated {metric} on {iface}, impacting {session}s for subscribers in {region}.",
        "Backhaul transport failure on {vendor} {node} at {site}. Degraded {iface} quality caused {proto} session instability and packet loss for users in {region}.",
        "{vendor} {node} backhaul fault at {site}. {iface} degradation increased {metric} beyond SLA threshold, causing {session} quality issues in {region}.",
    ],
    "core_network_failure": [
        "{vendor} {node} lost connectivity to {ctrl} at {site}. {proto} failure caused mass {session} drops for subscribers in {region}.",
        "Core network {ctrl} connectivity failure at {site}. Loss of {proto} signaling caused {session} management disruption for users in {region}.",
        "{vendor} {node} {proto} failure toward {ctrl} at {site}. {session} establishment failures caused service outage for users in {region}.",
    ],
    "power_environmental": [
        "{vendor} {node} at {site} reported power supply fault. Environmental alarm activated equipment protection, reducing {iface} capacity and impacting {session}s in {region}.",
        "Power failure on {vendor} {node} at {site}. Mains interruption triggered battery backup, causing partial {iface} shutdown and {metric} degradation in {region}.",
        "{vendor} {node} at {site} experienced environmental fault. Temperature or power anomaly triggered protection mode, reducing capacity and causing service degradation in {region}.",
    ],
}

_TELSTRA_RES = {
    "signal_degradation": [
        "Field team inspected {vendor} {node} antenna system at {site}. RF parameters recalibrated, feeder connections verified, {metric} restored to nominal. Service resumed after maintenance.",
        "Remote diagnostic on {vendor} {node}. Transmit power and antenna tilt adjusted, {metric} optimised. Coverage restored to planned contour after configuration update.",
        "RF audit completed on {vendor} {node} at {site}. Antenna connector reseated and feeder cable replaced. {metric} confirmed within specification. Incident resolved.",
    ],
    "interface_failure": [
        "{iface} restored after {vendor} {node} {proto} session reset. Configuration verified, signaling stack restarted. {session}s re-established. Root cause: transient {proto} timer misconfiguration.",
        "{vendor} {node} {iface} fault cleared by resetting {proto} stack. Verified {ctrl} connectivity and re-established all active {session}s. Stable operation confirmed.",
        "{vendor} {iface} failure investigated. {proto} parameter mismatch corrected. {session} continuity restored after {iface} re-initialisation and verification.",
    ],
    "hardware_fault": [
        "Faulty hardware component on {vendor} {node} replaced at {site}. {iface} functionality verified post-repair. {metric} confirmed within normal range. Full service restored.",
        "{vendor} maintenance replaced defective {node} hardware module. Post-replacement verification confirmed {iface} stability and {metric} within specification.",
        "Emergency hardware replacement completed on {vendor} {node}. Defective unit swapped and configuration restored. {iface} and {metric} confirmed normal. Service fully restored.",
    ],
    "software_config_error": [
        "{vendor} {node} issue resolved by vendor-recommended patch. {proto} process restarted and configuration corrected. {session} establishment restored to normal.",
        "Configuration error on {vendor} {node} corrected after {proto} log analysis. Parameter updates applied, {session} management verified. System stable post-fix.",
        "{vendor} software fix applied to resolve {proto} process exception. Configuration rollback validated. {session} restoration confirmed. Root cause sent to vendor TAC.",
    ],
    "capacity_congestion": [
        "Capacity issue resolved by load balancing {session}s across {vendor} {node} resources. Short-term congestion relief applied. Long-term capacity upgrade scheduled.",
        "{vendor} {node} congestion cleared by activating additional {iface} capacity and adjusting {proto} scheduler. {metric} utilisation normalised.",
        "Traffic redistribution applied on {vendor} {node}. {session} admission control tuned. {metric} reduced to acceptable level. Capacity expansion request submitted.",
    ],
    "sync_timing_failure": [
        "Synchronisation restored on {vendor} {node} by switching to backup timing reference. {metric} verified within specification. Primary source repaired and reactivated.",
        "{vendor} {node} clock issue resolved. Timing source failover executed, {iface} synchronisation re-established. {metric} confirmed within ITU-T specification.",
        "Timing fault cleared on {vendor} {node}. Synchronisation chain verified, faulty reference replaced. {metric} restored. {iface} stability confirmed.",
    ],
    "backhaul_transport": [
        "Backhaul fault resolved after {vendor} transport team repaired {iface}. {metric} verified within SLA. {session}s re-established. Root cause: physical layer degradation.",
        "{vendor} {node} backhaul restored after {iface} fault cleared. Traffic re-routed over redundant link during repair. {metric} confirmed normal post-restoration.",
        "Transport maintenance completed on {vendor} backhaul. {iface} quality restored, {metric} within specification. {session} continuity confirmed.",
    ],
    "core_network_failure": [
        "{vendor} {ctrl} connectivity restored after {proto} session re-establishment. {session} management resumed and affected subscribers re-registered.",
        "Core {vendor} {ctrl} fault cleared. {proto} signaling path restored, {session} establishment verified. Redundancy activated to minimise impact.",
        "{vendor} {node} reconnected to {ctrl} after {proto} failure resolution. {session} restoration verified. Monitoring enhanced to detect recurrence.",
    ],
    "power_environmental": [
        "{vendor} {node} power fault resolved after replacement of faulty power module. {iface} capacity fully restored. Environmental monitoring confirmed normal conditions.",
        "Power supply restored to {vendor} {node}. Battery backup tested and verified. {iface} and {metric} confirmed operational. Preventive maintenance scheduled.",
        "{vendor} {node} environmental alarm cleared after cooling and power restored. {iface} functionality verified. {metric} within specification. Site inspection completed.",
    ],
}

_CATEGORY_SERVICE_IMPACT = {
    "signal_degradation":    ["Mobile broadband throughput reduced", "Voice calls affected", "Data sessions degraded"],
    "interface_failure":     ["Data sessions degraded", "Voice calls affected", "Roaming services unavailable"],
    "hardware_fault":        ["Mobile broadband throughput reduced", "Data sessions degraded", "Enterprise VPN disrupted"],
    "software_config_error": ["Voice calls affected", "SMS delivery delayed", "Data sessions degraded"],
    "capacity_congestion":   ["Mobile broadband throughput reduced", "Video streaming interrupted", "Cloud-hosted applications unreachable"],
    "sync_timing_failure":   ["Voice calls affected", "Data sessions degraded", "IoT connectivity lost"],
    "backhaul_transport":    ["Inter-site backhaul degraded", "Mobile broadband throughput reduced", "Enterprise VPN disrupted"],
    "core_network_failure":  ["Voice calls affected", "Emergency services impacted", "Data sessions degraded"],
    "power_environmental":   ["Mobile broadband throughput reduced", "Voice calls affected", "Fixed broadband users affected"],
}


def load_and_transform_telstra(start_seq: int) -> list[dict]:
    """
    Joins all 5 Telstra labelled files on `id` and transforms them into
    the 10-field incident schema. Uses only train.csv rows (7,381) since
    test.csv has no fault_severity labels.
    """
    import pandas as pd

    base = os.path.join(BASE_DIR, "data")

    def _csv(name: str) -> str:
        return os.path.join(base, f"{name}.csv", f"{name}.csv")

    required = ["train", "event_type", "log_feature", "resource_type", "severity_type"]
    for name in required:
        if not os.path.isfile(_csv(name)):
            print(f"  [SKIP] Telstra file not found: {_csv(name)}")
            return []

    print("  Reading Telstra files...")
    train    = pd.read_csv(_csv("train"))
    ev_df    = pd.read_csv(_csv("event_type"))
    lf_df    = pd.read_csv(_csv("log_feature"))
    res_df   = pd.read_csv(_csv("resource_type"))
    sev_df   = pd.read_csv(_csv("severity_type"))

    # Aggregate multi-row features per id
    # event_type: take most common event per id (primary fault signal)
    ev_primary = (ev_df.groupby("id")["event_type"]
                  .agg(lambda x: x.mode().iloc[0] if len(x) else x.iloc[0])
                  .reset_index()
                  .rename(columns={"event_type": "primary_event"}))
    # all event types for enrichment
    ev_all = (ev_df.groupby("id")["event_type"]
              .apply(lambda x: list(x.unique()))
              .reset_index()
              .rename(columns={"event_type": "all_events"}))

    # log_feature: total volume per id (proxy for alarm intensity)
    lf_agg = (lf_df.groupby("id")["volume"]
              .sum()
              .reset_index()
              .rename(columns={"volume": "total_log_volume"}))

    # resource_type: primary type per id
    res_primary = (res_df.groupby("id")["resource_type"]
                   .agg(lambda x: x.mode().iloc[0] if len(x) else x.iloc[0])
                   .reset_index())

    # severity_type: primary type per id
    sev_primary = (sev_df.groupby("id")["severity_type"]
                   .agg(lambda x: x.mode().iloc[0] if len(x) else x.iloc[0])
                   .reset_index())

    # Join everything onto train
    df = (train
          .merge(ev_primary,  on="id", how="left")
          .merge(ev_all,      on="id", how="left")
          .merge(lf_agg,      on="id", how="left")
          .merge(res_primary, on="id", how="left")
          .merge(sev_primary, on="id", how="left"))

    print(f"  Joined dataset: {len(df)} rows, cols: {list(df.columns)}")

    rows = []
    rng  = random.Random(42)   # deterministic

    for _, r in df.iterrows():
        record_id    = int(r["id"])
        fault_sev    = str(int(r.get("fault_severity", 0)))
        location_raw = str(r.get("location", "location 1"))
        event_raw    = str(r.get("primary_event", "event_type 1"))
        resource_raw = str(r.get("resource_type", "resource_type 1"))
        severity_raw = str(r.get("severity_type", "severity_type 1"))
        log_volume   = int(r.get("total_log_volume", 1) or 1)

        # Derive structured fields
        severity_choices = _FAULT_TO_SEVERITY.get(fault_sev, ["MEDIUM"])
        severity  = rng.choice(severity_choices)
        technology = _RESOURCE_TO_TECH.get(resource_raw.strip(), "RAN")
        vendor     = _SEVERITY_TO_VENDOR.get(severity_raw.strip(), "Ericsson")

        # Stable region from location number
        loc_num = 0
        m = re.search(r"(\d+)", location_raw)
        if m:
            loc_num = int(m.group(1))
        region = _TELSTRA_REGIONS[loc_num % len(_TELSTRA_REGIONS)]
        site   = f"SITE-{region[:3].upper()}-{loc_num:04d}"

        # Fault category from primary event type
        ev_num = 1
        m2 = re.search(r"(\d+)", event_raw)
        if m2:
            ev_num = int(m2.group(1))
        category = _event_to_category(ev_num)

        # Technology vocabulary
        vocab = _TECH_VOCAB.get(technology, _TECH_VOCAB["RAN"])

        fmt = dict(
            vendor=vendor, node=vocab["node"], iface=vocab["iface"],
            metric=vocab["metric"], proto=vocab["proto"],
            session=vocab["session"], ctrl=vocab["ctrl"],
            region=region, site=site,
        )

        desc_tmpl = rng.choice(_TELSTRA_DESC[category])
        res_tmpl  = rng.choice(_TELSTRA_RES[category])
        description = desc_tmpl.format(**fmt)
        resolution  = res_tmpl.format(**fmt)

        # Outage duration — scale with log volume and severity
        lo, hi = OUTAGE_RANGES[severity]
        volume_factor = min(log_volume / 50.0, 3.0)   # cap multiplier at 3×
        duration = int(min(lo + (hi - lo) * volume_factor * rng.random(), hi))

        # Timestamp — deterministic from record id
        base_dt = datetime(2024, 1, 1)
        offset  = timedelta(hours=record_id % 8760)   # spread over ~1 year
        ts      = (base_dt + offset).strftime("%Y-%m-%d %H:%M:%S")

        alarm_id = f"ALM-TLS-{record_id:05d}"

        service_impact = rng.choice(_CATEGORY_SERVICE_IMPACT[category])

        rows.append({
            "alarm_id":             alarm_id,
            "incident_description": description,
            "network_region":       region,
            "technology_type":      technology,
            "severity":             severity,
            "outage_duration":      duration,
            "device_vendor":        vendor,
            "resolution_notes":     resolution,
            "timestamp":            ts,
            "service_impact":       service_impact,
        })

    print(f"  Transformed {len(rows)} incidents from Telstra dataset")
    return rows


# ── Fallback: manual CSV (Kaggle or any other source) ─────────────────────────

def load_manual_csv(path: str) -> list[dict]:
    import pandas as pd
    df = pd.read_csv(path, low_memory=False)
    print(f"  [OK]  Loaded manual CSV: {len(df)} rows, columns: {list(df.columns)}")
    return df.to_dict(orient="records")


def transform_manual_csv(raw_rows: list[dict], start_seq: int) -> list[dict]:
    """
    Best-effort transform for any CSV dropped into data/raw/.
    Looks for description-like and resolution-like columns by name.
    """
    DESC_KEYS = ["incident_description", "description", "fault_description",
                 "root_cause", "input", "text", "alarm_description", "event_description"]
    RES_KEYS  = ["resolution_notes", "resolution", "output", "resolution_summary",
                 "actions", "remedy", "fix", "solution"]

    # Identify columns
    all_cols  = list(raw_rows[0].keys()) if raw_rows else []
    cols_l    = {c.lower().strip(): c for c in all_cols}

    desc_col = next((cols_l[k] for k in DESC_KEYS if k in cols_l), None)
    res_col  = next((cols_l[k] for k in RES_KEYS  if k in cols_l), None)

    if not desc_col:
        # Use the longest text column
        text_cols = [c for c in all_cols if isinstance(raw_rows[0].get(c), str) and len(str(raw_rows[0].get(c, ""))) > 30]
        desc_col  = text_cols[0] if text_cols else None

    if not desc_col:
        print("  [SKIP]  Could not find a description column. Skipping manual CSV.")
        return []

    rows, seq = [], start_seq
    for r in raw_rows:
        desc = str(r.get(desc_col) or "").strip()
        res  = str(r.get(res_col) or "") .strip() if res_col else ""
        if not desc or len(desc) < 20:
            continue
        rows.append(build_row(seq, desc, res or "Resolved via standard troubleshooting procedure."))
        seq += 1
    print(f"  [OK]  Transformed {len(rows)} incidents from manual CSV")
    return rows


# ── Writer ─────────────────────────────────────────────────────────────────────

FIELDNAMES = [
    "alarm_id", "incident_description", "network_region",
    "technology_type", "severity", "outage_duration",
    "device_vendor", "resolution_notes", "timestamp", "service_impact",
]


def write_csv(rows: list[dict]) -> None:
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n✅  Wrote {len(rows):,} incidents → {OUTPUT_CSV}")


def print_summary(rows: list[dict]) -> None:
    from collections import Counter
    sev  = Counter(r["severity"]       for r in rows)
    tech = Counter(r["technology_type"] for r in rows)
    vend = Counter(r["device_vendor"]   for r in rows)
    print(f"\n   Severity    : {dict(sev)}")
    print(f"   Technology  : {dict(tech)}")
    print(f"   Vendors     : {dict(vend)}")
    print(f"\n   Next step   : python ingest_data.py")


# ── Entry point ────────────────────────────────────────────────────────────────

def find_raw_csv() -> str:
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    if os.path.isdir(raw_dir):
        for f in sorted(os.listdir(raw_dir)):
            if f.lower().endswith(".csv"):
                return os.path.join(raw_dir, f)
    return ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="",
                        help="Path to a raw CSV file to transform (optional)")
    parser.add_argument("--skip-hf", action="store_true",
                        help="Skip HuggingFace downloads (use only manual CSV)")
    args = parser.parse_args()

    all_rows: list[dict] = []
    seq = 1

    # ── Manual CSV override ────────────────────────────────────────────────────
    manual_path = args.input or find_raw_csv()
    if manual_path and os.path.isfile(manual_path):
        print(f"\n[Manual CSV] {manual_path}")
        raw = load_manual_csv(manual_path)
        rows = transform_manual_csv(raw, seq)
        all_rows.extend(rows)
        seq += len(rows)

    # ── HuggingFace sources ────────────────────────────────────────────────────
    if not args.skip_hf:
        print("\n[Source 1] greenwich157/5G_Faults_Full (HuggingFace)")
        raw1 = load_hf_5g_faults_full()
        if raw1:
            rows1 = transform_5g_faults_full(raw1, seq)
            all_rows.extend(rows1)
            seq += len(rows1)

        print("\n[Source 2] greenwich157/telco-5G-data-faults (HuggingFace)")
        raw2 = load_hf_telco_faults()
        if raw2:
            rows2 = transform_telco_faults(raw2, seq)
            all_rows.extend(rows2)
            seq += len(rows2)

        print("\n[Source 3] GoMask.ai Network Outage Incident Logs (sample)")
        raw3 = load_gomask_outage_sample()
        if raw3:
            rows3 = transform_gomask(raw3, seq)
            all_rows.extend(rows3)
            seq += len(rows3)

    # ── Telstra Network Disruption dataset (always attempted if files present) ──
    print("\n[Source 4] Telstra Network Disruption dataset (local)")
    rows4 = load_and_transform_telstra(seq)
    if rows4:
        all_rows.extend(rows4)
        seq += len(rows4)

    if not all_rows:
        print("\n[ERROR] No data loaded from any source.")
        print("  Tip: ensure internet connectivity, or provide a manual CSV:")
        print("       python prepare_dataset.py --input path/to/your_dataset.csv")
        sys.exit(1)

    print(f"\n[Summary] Total incidents collected: {len(all_rows):,}")
    write_csv(all_rows)
    print_summary(all_rows)


if __name__ == "__main__":
    main()
