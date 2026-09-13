"""Static ICAO/IATA carrier-code -> friendly-name lookup, used for the "operated by" line
(docs/features/status-card-requirements.md#SC-C1). AeroAPI gives us the operator's codes
(`operator_icao` / `operator_iata`) but not a display name, so this is a small hand-maintained table
covering common carriers — not exhaustive. Unknown codes degrade gracefully (caller falls back to
showing the raw code) rather than erroring.
"""

from __future__ import annotations

# Keyed by ICAO code (more reliably present on AeroAPI responses than IATA for regional/charter
# operators). Add to this as gaps show up in real usage rather than trying to be complete up front.
_OPERATOR_NAMES_BY_ICAO: dict[str, str] = {
    "AAL": "American Airlines",
    "ACA": "Air Canada",
    "ASA": "Alaska Airlines",
    "AAY": "Allegiant Air",
    "BAW": "British Airways",
    "DAL": "Delta Air Lines",
    "DLH": "Lufthansa",
    "EJA": "NetJets",
    "ENY": "Envoy Air",
    "FDX": "FedEx Express",
    "FFT": "Frontier Airlines",
    "HAL": "Hawaiian Airlines",
    "JBU": "JetBlue Airways",
    "JIA": "PSA Airlines",
    "NKS": "Spirit Airlines",
    "QXE": "Horizon Air",
    "RPA": "Republic Airways",
    "SCX": "Sun Country Airlines",
    "SKW": "SkyWest Airlines",
    "SWA": "Southwest Airlines",
    "UAL": "United Airlines",
    "UPS": "UPS Airlines",
}


def get_operator_name(operator_icao: str | None) -> str | None:
    """Friendly airline name for an ICAO operator code, or None if not in the table."""
    if not operator_icao:
        return None
    return _OPERATOR_NAMES_BY_ICAO.get(operator_icao.strip().upper())
