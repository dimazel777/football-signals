from datetime import datetime

from pari_client import get_upcoming_matches
from soccer365_corners import get_match_info

TARGET_ID = 69584100

SOCCER365_URL = (
    "https://soccer365.ru/live/"
    "match-fadjr-sepasi-persepolis-smotret-onlayn/"
)

def main():
    print("Проверяю доступность PARI...")

    pari_matches = get_upcoming_matches(limit=200)

    target = pari_matches[0]

print(f"Матч PARI: {target.get('matchInfo', {}).get('homeTeam', {}).get('name')} — "
      f"{target.get('matchInfo', {}).get('awayTeam', {}).get('name')}")

    info = target.get("matchInfo") or {}

    home = (info.get("homeTeam") or {}).get("name", "?")
    away = (info.get("awayTeam") or {}).get("name", "?")

    print(f"Матч PARI: {home} — {away}")
    print(f"Время PARI: {info.get('startDate')}")

    print("\nПроверяю отдельную страницу Soccer365...")

    try:
        soccer_info = get_match_info(SOCCER365_URL)

        pari_time = datetime.fromisoformat(
            info["startDate"].replace("Z", "+00:00")
        ).timestamp()

        soccer_time = int(soccer_info["kickoff"])

        print("СТРАНИЦА ДОСТУПНА")
        print(f"Время Soccer365: {soccer_time}")
        print(f"Разница во времени: {abs(pari_time - soccer_time)} секунд")
        print(f"ID домашней команды: {soccer_info['home_id']}")
        print(f"ID гостевой команды: {soccer_info['away_id']}")

    except Exception as error:
        print("ОШИБКА ДОСТУПА К ОТДЕЛЬНОЙ СТРАНИЦЕ:")
        print(repr(error))

if __name__ == "__main__":
    main()
