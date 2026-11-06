from pari_client import get_upcoming_matches
from collect_today_matches import main as get_soccer365_matches
from match_finder import find_soccer365_match

def main():
    print("Загружаю матчи PARI...")
    pari_matches = get_upcoming_matches(limit=200)

    print("Загружаю матчи Soccer365...")
    soccer_matches = get_soccer365_matches()

    matched = []
    unmatched = []

    print("\n========== МАССОВАЯ ПРОВЕРКА ==========")

    for pari_match in pari_matches:
        info = pari_match.get("matchInfo") or {}

        home = (info.get("homeTeam") or {}).get("name", "?")
        away = (info.get("awayTeam") or {}).get("name", "?")

        result = find_soccer365_match(
            pari_match,
            soccer_matches
        )

        if result:
            matched.append((home, away))
            print(f"НАЙДЕН: {home} — {away}")
        else:
            tournament = info.get("tournament") or {}
            country = (tournament.get("country") or {}).get("name", "?")
            start = info.get("startDate", "?")

            unmatched.append(
                (home, away, country, tournament.get("name", "?"), start)
            )

    print("\n========== ИТОГИ ==========")
    print(f"Матчей PARI: {len(pari_matches)}")
    print(f"Найдено совпадений: {len(matched)}")
    print(f"Не найдено: {len(unmatched)}")

    print("\nПервые 20 ненайденных матчей:")

    for home, away, country, tournament, start in unmatched[:20]:
        print(
            f"{home} — {away} | {country} | "
            f"{tournament} | {start}"
        )

if __name__ == "__main__":
    main()
