from datetime import datetime, timezone

from pari_client import get_upcoming_matches
from soccer365_corners import get_match_info

MATCH_ID = 69584100
MATCH_URL = "https://soccer365.ru/live/match-fadjr-sepasi-persepolis-smotret-onlayn/"

def main():
    print("========== PARI ==========")

    matches = get_upcoming_matches(limit=200)
    pari_match = None

    for match in matches:
        info = match.get("matchInfo") or {}

        if info.get("eventId") == MATCH_ID:
            pari_match = info
            break

    if pari_match:
        pari_time = datetime.fromisoformat(pari_match["startDate"])

        print("Матч:", pari_match["homeTeam"]["name"], "-", pari_match["awayTeam"]["name"])
        print("Время PARI:", pari_time.isoformat())
        print("Время PARI в UTC:", pari_time.astimezone(timezone.utc).isoformat())
    else:
        print("Матч не найден в PARI")

    print("\n========== SOCCER365 ==========")

    info = get_match_info(MATCH_URL)

    print("Матч:", info["title"])
    print("Unix timestamp:", info["kickoff"])
    print(
        "Время Soccer365 в UTC:",
        datetime.fromtimestamp(info["kickoff"], timezone.utc).isoformat()
    )

if __name__ == "__main__":
    main()
