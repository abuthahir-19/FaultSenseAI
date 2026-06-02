from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict
from loguru import logger


def correlate_alarms(incidents: List[Dict[str, Any]], time_window_hours: int = 24) -> List[Dict[str, Any]]:
    """
    Group incidents into clusters by (network_region + technology_type).
    Returns clusters with >= 2 incidents.
    """
    if not incidents:
        return []

    clusters = defaultdict(list)
    for inc in incidents:
        region = inc.get("network_region", "unknown")
        tech = inc.get("technology_type", "unknown")
        key = f"{region}|{tech}"
        clusters[key].append(inc)

    result = []
    for key, group in clusters.items():
        if len(group) < 2:
            continue

        region, tech = key.split("|", 1)
        vendors = [g.get("device_vendor", "unknown") for g in group]
        severities = [g.get("severity", "MEDIUM") for g in group]
        alarm_ids = [g.get("alarm_id", "") for g in group]
        dominant_vendor = max(set(vendors), key=vendors.count)
        max_severity = _max_severity(severities)

        timestamps = []
        for g in group:
            ts_str = str(g.get("timestamp", ""))
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                timestamps.append(ts)
            except Exception:
                pass

        time_span_hours = None
        if len(timestamps) >= 2:
            time_span_hours = (max(timestamps) - min(timestamps)).total_seconds() / 3600

        cluster = {
            "cluster_id": f"CLU-{region[:3].upper()}-{tech[:3].upper()}",
            "network_region": region,
            "technology_type": tech,
            "incident_count": len(group),
            "alarm_ids": alarm_ids,
            "dominant_vendor": dominant_vendor,
            "max_severity": max_severity,
            "has_critical": "CRITICAL" in severities,
            "time_span_hours": time_span_hours,
            "summary": (
                f"{len(group)} correlated {tech} alarms in {region} "
                f"from {dominant_vendor} (max severity: {max_severity})"
            ),
        }
        result.append(cluster)
        logger.debug(f"Cluster: {cluster['cluster_id']} — {len(group)} incidents")

    result.sort(key=lambda c: c["incident_count"], reverse=True)
    return result


def _max_severity(severities: List[str]) -> str:
    order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    return max(severities, key=lambda s: order.get(s.upper(), 0), default="MEDIUM")
