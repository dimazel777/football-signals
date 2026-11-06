from pari_client import get_upcoming_matches
from collect_today_matches import main as get_soccer365_matches
from match_finder import find_soccer365_match

TARGET_ID = 69584100

def main():
    pari_matches = get_upcoming_matches(limit=200)
    soccer_matches = get_soccer365_matches()

    target = next(
        (
            match for match in pari_matches
            if (match.get("matchInfo") or {}).get("eventId") == TARGET_ID
        ),
        None
    )

    if not target:
        print("Матч не найден в PARI")
        return

    print("Проверяем Персеполис — Фаджр Сепаси")

    result = find_soccer365_match(target, soccer_matches)

    if result:
        print("МАТЧ НАЙДЕН:")
        print(result["match"])
        print(result["url"])
    else:
        print("МАТЧ НЕ НАЙДЕН")

if __name__ == "__main__":
    main()
