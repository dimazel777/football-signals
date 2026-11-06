import json
import os
from pathlib import Path

STATE_FILE = Path("data/signal_state.json")

def load_state():
    """Загружает сохранённое состояние."""
    if not STATE_FILE.exists():
        return {
            "signals": {},
            "daily_summaries": []
        }

    with STATE_FILE.open("r", encoding="utf-8") as file:
        state = json.load(file)

    state.setdefault("signals", {})
    state.setdefault("daily_summaries", [])

    return state

def save_state(state):
    """Безопасно сохраняет состояние."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    temp_file = STATE_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2
        )

    os.replace(temp_file, STATE_FILE)

def signal_exists(state, match_id):
    """Проверяет, отправлялся ли сигнал по этому матчу."""
    return str(match_id) in state["signals"]

def add_signal(state, match_id, signal_data):
    """Добавляет новый сигнал."""
    match_id = str(match_id)

    if signal_exists(state, match_id):
        return False

    state["signals"][match_id] = {
        **signal_data,
        "status": "pending",
        "telegram_message_id": None,
        "result": None
    }

    save_state(state)
    return True

def update_telegram_message_id(state, match_id, message_id):
    """Сохраняет ID сообщения Telegram."""
    match_id = str(match_id)

    if match_id not in state["signals"]:
        return False

    state["signals"][match_id]["telegram_message_id"] = message_id
    save_state(state)
    return True

def update_signal_result(state, match_id, result):
    """Сохраняет результат сигнала: success или failed."""
    match_id = str(match_id)

    if match_id not in state["signals"]:
        return False

    if result not in ("success", "failed"):
        raise ValueError("Результат должен быть success или failed")

    state["signals"][match_id]["status"] = result
    state["signals"][match_id]["result"] = result

    save_state(state)
    return True

def mark_daily_summary_sent(state, date):
    """Отмечает, что итог за день уже отправлен."""
    date = str(date)

    if date in state["daily_summaries"]:
        return False

    state["daily_summaries"].append(date)
    save_state(state)
    return True
