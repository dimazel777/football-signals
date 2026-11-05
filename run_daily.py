import time

import collect_today_matches as collector
import soccer365_corners as analyzer
import telegram_publisher as telegram

def main():
    matches = collector.main()

    if not matches:
        print("\nМатчей для анализа нет.")
        return

    results = []

    print("\nНАЧИНАЮ АНАЛИЗ МАТЧЕЙ")
    print("=" * 60)

    for number, match in enumerate(matches, start=1):
        print(f"\nМатч {number}/{len(matches)}")

        try:
            result = analyzer.analyze_match(match["url"])

            if result:
                result["competition"] = match["competition"]
                result["country"] = match["country"]
                result["kickoff"] = match["kickoff"]
                results.append(result)

        except Exception as error:
            print(f"Ошибка анализа: {error}")

        time.sleep(0.5)

    results.sort(
        key=lambda item: item["expected_total_corners"],
        reverse=True
    )

    print("\n" + "=" * 60)
    print("ТОП-10 МАТЧЕЙ ПО ОЖИДАЕМОМУ ТОТАЛУ УГЛОВЫХ")
    print("=" * 60)

    for number, result in enumerate(results[:10], start=1):
        print(f"\n{number}. {result['match']}")
        print(f"   Турнир: {result['competition']}")
        print(f"   Время: {result['kickoff']}")
        print(
            f"   Ожидаемый тотал: "
            f"{result['expected_total_corners']}"
        )

        for line, probability in result["probabilities"].items():
            print(f"   ТБ {line}: {probability}%")

    print(f"\nВсего найдено матчей: {len(matches)}")
    print(f"Успешно проанализировано: {len(results)}")
    print(f"В итоговом списке: {min(10, len(results))}")

    print(
        "\nВнимание: вероятности пока не откалиброваны "
        "на достаточной исторической выборке."
    )

    telegram.send_report(results)

if __name__ == "__main__":
    main()