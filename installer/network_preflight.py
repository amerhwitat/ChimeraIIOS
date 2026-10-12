#!/usr/bin/env python3
"""Conservative, privacy-preserving installer network preflight recommendations.

Consumes a local hardware/connectivity report only. It never collects or stores
network credentials and does not recommend blind driver installation.
"""
from __future__ import annotations

from typing import Any


def recommend(report: dict[str, Any]) -> list[dict[str, str]]:
    """Return actionable next steps based on detected interfaces and connectivity."""
    connectivity = report.get("connectivity") or {}
    devices = report.get("devices") or []
    if connectivity.get("internet_ready") is True:
        return [{
            "title": "Internet ready — continue installation",
            "detail": "Connectivity is available. Continue; keep package downloads optional if desired.",
            "source": "connectivity-probe",
        }]

    recommendations: list[dict[str, str]] = []
    if not devices:
        recommendations.append({
            "title": "No network interface detected",
            "detail": "Check firmware/device visibility, cable or radio switch, and rerun hardware detection.",
            "source": "hardware-rules",
        })
        recommendations.append({
            "title": "Continue offline if supported",
            "detail": "Use local installation media and configure networking after installation.",
            "source": "installer-policy",
        })
        return recommendations

    for device in devices:
        if not isinstance(device, dict):
            continue
        name = str(device.get("name") or "unnamed interface")
        kind = str(device.get("type") or "unknown").lower()
        bound = device.get("driver_bound") is True
        if not bound:
            recommendations.append({
                "title": f"Identify driver for {name}",
                "detail": "Collect device ID/modalias and compare it with trusted hardware rules; do not install a guessed driver.",
                "source": "hardware-rules",
            })
        elif kind in {"wifi", "wireless", "wlan"}:
            recommendations.append({
                "title": f"Configure Wi-Fi for {name}",
                "detail": "Select a visible network in the installer and enter credentials only in the secure network UI.",
                "source": "network-configuration",
            })
        else:
            recommendations.append({
                "title": f"Check connectivity for {name}",
                "detail": "Verify link state, DHCP/address assignment, and DNS using local diagnostics.",
                "source": "network-configuration",
            })

    if not recommendations:
        recommendations.append({
            "title": "Inspect detected network hardware",
            "detail": "Review interface type, driver binding, link state, and connectivity diagnostics.",
            "source": "hardware-rules",
        })
    return recommendations
