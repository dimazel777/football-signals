import os
import requests

TELEGRAM_API = "https://api.telegram.org"

def get_credentials():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHANNEL_ID")

    if not token or not chat_id:
        raise RuntimeError("Не найдены настройки Telegram в GitHub Secrets")

    return token, chat_id

def send_signal(match_name, line, odds, probability, kickoff):
    """Отправляет отдельный сигнал в Telegram."""

    token, chat_id = get_credentials()

    text = (
        "⚽ СИГНАЛ НА УГЛОВЫЕ\n\n"
        f"Матч: {match_name}\n"
        f"Рынок: Тотал угловых — Больше {line}\n"
        f"Коэффициент PARI: {odds:.2f}\n"
        f"Вероятность модели: {probability * 100:.1f}%\n"
        f"Начало матча: {kickoff}\n\n"
        "⏳ Результат будет добавлен после окончания матча."
    )

    response = requests.post(
        f"{TELEGRAM_API}/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
        },
        timeout=30,
    )
    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"Ошибка Telegram: {result}")

    return result["result"]["message_id"]

def update_signal_message(message_id, result):
    """Добавляет результат в первоначальное сообщение."""

    token, chat_id = get_credentials()

    if result == "success":
        mark = "✅"
        description = "СИГНАЛ ЗАШЁЛ"
    elif result == "failed":
        mark = "❌"
        description = "СИГНАЛ НЕ ЗАШЁЛ"
    else:
        raise ValueError("Неизвестный результат сигнала")

    response = requests.post(
        f"{TELEGRAM_API}/bot{token}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": (
                f"Результат матча: {description}\n\n"
                f"Исходное сообщение сохранено выше.\n{mark}"
            ),
        },
        timeout=30,
    )

    response.raise_for_status()

    result_data = response.json()

    if not result_data.get("ok"):
        raise RuntimeError(f"Ошибка Telegram: {result_data}")

    return True

def send_daily_summary(date, success_count, failed_count):
    """Отправляет итоговую статистику за день."""

    token, chat_id = get_credentials()

    total = success_count + failed_count
    percentage = (
        success_count / total * 100
        if total > 0
        else 0
    )

    text = (
        f"Сигналы за {date}\n"
        f"{success_count} ✅\n"
        f"{failed_count} ❌\n"
        f"{percentage:.1f}% успешных сигналов"
    )

    response = requests.post(
        f"{TELEGRAM_API}/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
        },
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"Ошибка Telegram: {result}")

    return result["result"]["message_id"]
  
