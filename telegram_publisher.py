import os
import requests

def send_report(results):
    results = sorted(
        results,
        key=lambda item: item["expected_total_corners"],
        reverse=True
    )[:10]

    if not results:
        message = (
            "⚽ FOOTBALL SIGNALS\n\n"
            "Сегодня нет матчей с достаточными данными для анализа."
        )
    else:
        lines = [
            "⚽ FOOTBALL SIGNALS",
            "ПРЕДМАТЧЕВЫЙ ОБЗОР УГЛОВЫХ",
            ""
        ]

        for number, item in enumerate(results, start=1):
            lines.extend([
                f"{number}. {item['match']}",
                f"Турнир: {item.get('competition', '—')}",
                f"Страна: {item.get('country', '—')}",
                f"Начало: {item.get('kickoff', '—')}",
                f"Ожидаемый тотал: {item['expected_total_corners']}",
                (
                    f"История: дома — {item['home_matches_count']}, "
                    f"в гостях — {item['away_matches_count']} матчей"
                ),
                "Оценки модели на ТБ:"
            ])

            for line, probability in item["probabilities"].items():
                lines.append(f"  {line}: {probability}%")

            lines.append("")

        lines.extend([
            "⚠️ Вероятности предварительные и не откалиброваны.",
            "Статистическая оценка не гарантирует результат."
        ])

        message = "\n".join(lines)

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    channel_id = os.environ["TELEGRAM_CHANNEL_ID"]

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": channel_id, "text": message},
        timeout=30
    )
    response.raise_for_status()

    if not response.json().get("ok"):
        raise RuntimeError("Telegram не подтвердил отправку.")

    print("Отчёт опубликован в Telegram.")
