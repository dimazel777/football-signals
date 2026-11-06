import re
from difflib import SequenceMatcher

from soccer365_corners import get_match_info

def transliterate(name):
    """Приближённо переводит кириллицу в латиницу для сравнения названий."""
    replacements = {
        "дж": "j", "ч": "ch", "ш": "sh", "щ": "shch",
        "ж": "zh", "х": "h", "ц": "ts", "ю": "yu",
        "я": "ya", "ё": "yo", "й": "y", "э": "e",
        "ъ": "", "ь": ""
    }

    name = name.lower()

    for source, target in replacements.items():
        name = name.replace(source, target)

    result = []
    for char in name:
        if "а" <= char <= "я":
            result.append({
                "а": "a", "б": "b", "в": "v", "г": "g",
                "д": "d", "е": "e", "з": "z", "и": "i",
                "к": "k", "л": "l", "м": "m", "н": "n",
                "о": "o", "п": "p", "р": "r", "с": "s",
                "т": "t", "у": "u", "ф": "f"
            }.get(char, char))
        else:
            result.append(char)

    return "".join(result).replace("dzh", "j")

def normalize_team_name(name):
    if not name:
        return ""

    name = transliterate(name)
    return re.sub(r"[^a-z0-9]", "", name)

def name_similarity(name1, name2):
    first = normalize_team_name(name1)
    second = normalize_team_name(name2)

    if not first or not second:
        return 0.0

    return SequenceMatcher(None, first, second).ratio()

def extract_team_names(match_text):
    """Извлекает названия команд из строки Soccer365."""

    if not match_text:
        return None, None

    text = match_text.strip()

    # Убираем время в начале строки.
    text = re.sub(r"^\s*\d{1,2}:\d{2}\s*", "", text)

    # Убираем обозначение тура в конце строки.
    text = re.sub(
        r"\s+-\s+\d+\s*[-–]?\s*(?:й|я|ый)?\s*тур.*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    parts = re.split(r"\s+[—–-]\s+", text, maxsplit=1)

    if len(parts) != 2:
        return None, None

    return parts[0].strip(), parts[1].strip()

def find_soccer365_match(pari_match, soccer_matches):
    """
    Ищет матч Soccer365 по командам и точному времени начала.

    Возвращает объект Soccer365 или None.
    """

    info = pari_match.get("matchInfo") or {}

    home_team = (info.get("homeTeam") or {}).get("name")
    away_team = (info.get("awayTeam") or {}).get("name")

    if not home_team or not away_team or not info.get("startDate"):
        return None

    candidates = []

    for soccer_match in soccer_matches:

        soccer_home, soccer_away = extract_team_names(
            soccer_match.get("match", "")
        )

        if not soccer_home or not soccer_away:
            continue

        home_similarity = name_similarity(home_team, soccer_home)
        away_similarity = name_similarity(away_team, soccer_away)

        # Порядок команд должен совпадать.
        if home_similarity < 0.72 or away_similarity < 0.72:
            continue

        score = (home_similarity + away_similarity) / 2

        url = soccer_match.get("url")

        if not url:
            continue

        try:
            soccer_info = get_match_info(url)

            pari_timestamp = int(
                __import__("datetime").datetime.fromisoformat(
                    info["startDate"].replace("Z", "+00:00")
                ).timestamp()
            )

            soccer_timestamp = int(soccer_info["kickoff"])

            difference = abs(pari_timestamp - soccer_timestamp)

        except Exception as error:
            print(f"Ошибка проверки времени матча: {error}")
            continue

        # Допускаем максимум 5 минут разницы.
        if difference > 300:
            continue

        candidates.append({
            "match": soccer_match,
            "score": score,
            "time_difference": difference
        })

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            -item["score"],
            item["time_difference"]
        )
    )

    # Не выбираем матч, если два варианта почти одинаково подходят.
    if len(candidates) > 1:
        first = candidates[0]
        second = candidates[1]

        if (
            first["score"] - second["score"] < 0.05
            and abs(
                first["time_difference"]
                - second["time_difference"]
            ) < 60
        ):
            return None

    return candidates[0]["match"]
