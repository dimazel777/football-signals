from pari_client import get_upcoming_matches
from collect_today_matches import main as get_soccer365_matches

def main():
    print("\n========== ДИАГНОСТИКА PARI ==========\n")

    try:
        pari_matches = get_upcoming_matches(limit=200)

        print(f"Получено матчей PARI: {len(pari_matches)}")

        for match in pari_matches[:15]:
            info = match.get("matchInfo") or {}

            home = (info.get("homeTeam") or {}).get("name")
            away = (info.get("awayTeam") or {}).get("name")

            print(
                f"{home} — {away} | "
                f"{info.get('startDate')} | "
                f"ID: {info.get('eventId')}"
            )

    except Exception as error:
        print(f"Ошибка PARI: {error}")

    print("\n========== ДИАГНОСТИКА SOCCER365 ==========\n")

    try:
        soccer_matches = get_soccer365_matches()

        if not soccer_matches:
            print("Матчи Soccer365 не найдены.")
            return

        print(f"\nПолучено матчей Soccer365: {len(soccer_matches)}")

        for match in soccer_matches[:15]:
            print(
                f"{match['match']} | "
                f"{match['kickoff']} | "
                f"{match['country']} | "
                f"{match['url']}"
            )

    except Exception as error:
        print(f"Ошибка Soccer365: {error}")

if __name__ == "__main__":
    main()
