import re
from datetime import datetime
from difflib import SequenceMatcher

def normalize_team_name(name):
    """Приводит название команды к единому виду."""
    if not name:
        return ""

    name = name.lower().strip()
    name = re.sub(r"[^a-zа-яё0-9]", "", name)

    return name

def name_similarity(name1, name2):
    """Оценивает сходство названий команд."""
    first = normalize_team_name(name1)
    second = normalize_team_name(name2)

    if not first or not second:
        return 0.0

    return SequenceMatcher(None, first, second).ratio()

def time_difference_minutes(pari_start, soccer_kickoff):
    """
    Сравнивает время начала матча.
    Время Soccer365 пока рассматривается как локальное время расписания.
    """
    try:
        pari_time = datetime.fromisoformat(
            pari_start.replace("Z", "+00:00")
        )

        pari_minutes = pari_time.hour * 60 + pari_time.minute

        hours, minutes = map(
            int,
            soccer_kickoff.split(":")
        )

        soccer_minutes = hours * 60 + minutes

        difference = abs(pari_minutes - soccer_minutes)

        # Учитываем переход через полночь.
        return min(difference, 1440 - difference)

    except (ValueError, AttributeError, TypeError):
        return None

def find_soccer365_match(pari_match, soccer_matches):
    """
    Ищет соответствующий матч Soccer365 для матча PARI.

    Возвращает найденный объект Soccer365 или None.
    """

    info = pari_match.get("matchInfo") or {}

    home_team = (info.get("homeTeam") or {}).get("name")
    away_team = (info.get("awayTeam") or {}).get("name")
    start_date = info.get("startDate")

    if not home_team or not away_team or not start_date:
        return None

    candidates = []

    for soccer_match in soccer_matches:
        soccer_home, separator, soccer_away = (
            soccer_match.get("match", "").partition(" - ")
        )

        if not separator:
            soccer_home, separator, soccer_away = (
                soccer_match.get("match", "").partition(" — ")
            )

        if not separator:
            continue

        home_similarity = name_similarity(
            home_team,
            soccer_home
        )

        away_similarity = name_similarity(
            away_team,
            soccer_away
        )

        # Проверяем также обратный порядок команд.
        direct_score = (
            home_similarity + away_similarity
        ) / 2

        reverse_score = (
            name_similarity(home_team, soccer_away)
            + name_similarity(away_team, soccer_home)
        ) / 2

        if reverse_score > direct_score:
            continue

        if home_similarity < 0.75 or away_similarity < 0.75:
            continue

        difference = time_difference_minutes(
            start_date,
            soccer_match.get("kickoff")
        )

        if difference is None or difference > 180:
            continue

        candidates.append({
            "match": soccer_match,
            "score": direct_score,
            "time_difference": difference,
        })

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            -item["score"],
            item["time_difference"]
        )
    )

    # Если два кандидата практически одинаково подходят,
    # не выбираем матч наугад.
    if len(candidates) > 1:
        first = candidates[0]
        second = candidates[1]

        if (
            first["score"] - second["score"] < 0.05
            and abs(
                first["time_difference"]
                - second["time_difference"]
            ) < 15
        ):
            return None

    return candidates[0]["match"]
