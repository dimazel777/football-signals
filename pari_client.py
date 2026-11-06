import requests

API_URL = "https://api.sstats.net/Pari/matches"

# Только тотал угловых за весь матч, исход Over (ТБ).
PARI_CORNER_OVER_IDS = {
    737: 8.5,
    739: 9.5,
    741: 10.5,
    743: 11.5,
    745: 12.5,
}

MIN_ODDS = 1.50

def get_upcoming_matches(limit=200, offset=0):
    params = {
        "upcoming": "true",
        "includeOdds": "true",
        "limit": limit,
        "offset": offset,
    }

    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()

    if payload.get("status") != "OK":
        raise RuntimeError(f"PARI API error: {payload}")

    return payload.get("data", [])

def get_qualifying_corner_lines(match):
    odds = match.get("currentOdds") or []
    qualifying = []

    for item in odds:
        outcome_id = item.get("id")
        coefficient = item.get("value")

        line = PARI_CORNER_OVER_IDS.get(outcome_id)

        if line is None or coefficient is None:
            continue

        coefficient = float(coefficient)

        if coefficient >= MIN_ODDS:
            qualifying.append({
                "line": line,
                "odds": coefficient,
                "outcome_id": outcome_id,
            })

    return qualifying
