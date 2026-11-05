import re
import sys
import time
from datetime import datetime, timedelta, timezone
from statistics import mean

import requests
from bs4 import BeautifulSoup


BASE = "https://soccer365.ru"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE + "/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get_soup(url):
    response = SESSION.get(url, timeout=25)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_match_info(match_url):
    soup = get_soup(match_url)
    html = str(soup)

    team_calls = re.findall(
        r"loadDataTeam\((\d+),this\.value,\d+\)", html
    )
    timestamps = re.findall(r"st:\s*(\d+)", html)

    if len(team_calls) < 2:
        raise ValueError("Не удалось определить ID обеих команд")

    if not timestamps:
        raise ValueError("Не удалось определить время матча")

    title = soup.title.get_text(" ", strip=True) if soup.title else match_url

    return {
        "home_id": int(team_calls[0]),
        "away_id": int(team_calls[1]),
        "kickoff": int(timestamps[0]),
        "title": title,
    }


def get_last_ten_ids(team_id, match_type, kickoff):
    url = BASE + "/index.php"
    params = {
        "c": "games",
        "a": "GetBlockFormTeam",
        "cl": team_id,
        "st": kickoff,
        "tm": match_type,
        "lm": 10,
    }

    response = SESSION.get(url, params=params, timeout=25)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    ids = []

    for link in soup.select("a.game_link"):
        game_id = link.get("dt-id")

        if not game_id:
            href = link.get("href", "")
            found = re.search(r"/games/(\d+)", href)
            if found:
                game_id = found.group(1)

        if game_id and game_id.isdigit() and game_id not in ids:
            ids.append(game_id)

    return ids[:10]


def get_match_corners(game_id):
    url = f"{BASE}/games/{game_id}/"
    soup = get_soup(url)

    info = soup.select_one(".info_block")
    if not info:
        return None

    date_text = info.get_text(" ", strip=True)
    date_match = re.search(
        r"(\d{2}\.\d{2}\.\d{4})\s+(\d{1,2}:\d{2})",
        date_text,
    )

    if not date_match:
        return None

    match_date = datetime.strptime(
        date_match.group(1), "%d.%m.%Y"
    ).date()

    corner_values = []

    for item in soup.select(".stats_item"):
        title = item.select_one(".stats_title")

        if not title or title.get_text(" ", strip=True) != "Угловые":
            continue

        values = item.select(".stats_inf")

        if len(values) < 2:
            continue

        try:
            home_corners = int(values[0].get_text(strip=True))
            away_corners = int(values[1].get_text(strip=True))
        except ValueError:
            continue

        corner_values.append((home_corners, away_corners))

    # Первый блок «Угловые» — статистика за весь матч.
    if not corner_values:
        return None

    return {
        "id": game_id,
        "date": match_date,
        "home_corners": corner_values[0][0],
        "away_corners": corner_values[0][1],
        "total_corners": sum(corner_values[0]),
    }


def collect_history(team_id, match_type, kickoff, role):
    game_ids = get_last_ten_ids(team_id, match_type, kickoff)

    kickoff_date = datetime.fromtimestamp(
        kickoff, timezone.utc
    ).date()
    cutoff_date = kickoff_date - timedelta(days=90)

    matches = []

    for game_id in game_ids:
        try:
            data = get_match_corners(game_id)

            if data is None:
                print(f"  Пропуск {game_id}: нет статистики угловых")
                continue

            if not (cutoff_date <= data["date"] < kickoff_date):
                print(f"  Пропуск {game_id}: дата вне окна 90 дней")
                continue

            matches.append(data)
            print(
                f"  {data['date']} | матч {game_id} | "
                f"угловые {data['home_corners']}–{data['away_corners']}"
            )

        except Exception as error:
            print(f"  Пропуск {game_id}: {error}")

        time.sleep(0.3)

    return matches


def calculate_prediction(home_matches, away_matches):
    if not home_matches or not away_matches:
        return None

    home_for = mean(m["home_corners"] for m in home_matches)
    home_against = mean(m["away_corners"] for m in home_matches)

    away_for = mean(m["away_corners"] for m in away_matches)
    away_against = mean(m["home_corners"] for m in away_matches)

    expected_home = (home_for + away_against) / 2
    expected_away = (away_for + home_against) / 2

    return {
        "home_team_corners_avg": round(home_for, 2),
        "home_team_conceded_avg": round(home_against, 2),
        "away_team_corners_avg": round(away_for, 2),
        "away_team_conceded_avg": round(away_against, 2),
        "expected_home_corners": round(expected_home, 2),
        "expected_away_corners": round(expected_away, 2),
        "expected_total_corners": round(expected_home + expected_away, 2),
    }


def poisson_over_probability(expected_total, line):
    import math

    # Для ТБ 8.5 нужно не менее 9 угловых
    min_corners = int(line) + 1

    probability = 0.0

    for k in range(min_corners):
        probability += (
            math.exp(-expected_total)
            * expected_total ** k
            / math.factorial(k)
        )

    return round((1 - probability) * 100, 1)

def analyze_match(match_url):
    info = get_match_info(match_url)

    print(f"\nАНАЛИЗ: {info['title']}")

    print("\nПоследние домашние матчи хозяев:")
    home_matches = collect_history(
        info["home_id"], 1, info["kickoff"], "home"
    )

    print("\nПоследние выездные матчи гостей:")
    away_matches = collect_history(
        info["away_id"], 2, info["kickoff"], "away"
    )

    print(
        f"\nНайдено матчей: хозяева {len(home_matches)}/10, "
        f"гости {len(away_matches)}/10"
    )

    if len(home_matches) < 5 or len(away_matches) < 5:
        print("Недостаточно данных — матч пропущен.")
        return None

    prediction = calculate_prediction(home_matches, away_matches)

    if not prediction:
        return None

    expected = prediction["expected_total_corners"]

    probabilities = {
        line: poisson_over_probability(expected, line)
        for line in [8.5, 9.5, 10.5, 11.5, 12.5]
    }

    return {
        "match": info["title"],
        "url": match_url,
        **prediction,
        "probabilities": probabilities,
        "home_matches_count": len(home_matches),
        "away_matches_count": len(away_matches),
    }

def main():
    if len(sys.argv) < 2:
        print(
            "Использование:\n"
            "python soccer365_corners.py "
            "https://soccer365.ru/live/ССЫЛКА_НА_МАТЧ/"
        )
        return

    match_url = sys.argv[1]

    print("Получаем информацию о предстоящем матче...")
    info = get_match_info(match_url)

    print(f"\nМатч: {info['title']}")
    print(f"ID хозяев: {info['home_id']}")
    print(f"ID гостей: {info['away_id']}")

    print("\nСобираем 10 последних домашних матчей хозяев...")
    home_matches = collect_history(
        info["home_id"], 1, info["kickoff"], "хозяева"
    )

    print("\nСобираем 10 последних выездных матчей гостей...")
    away_matches = collect_history(
        info["away_id"], 2, info["kickoff"], "гости"
    )

    print("\nИТОГ СБОРА")
    print(f"Домашние матчи хозяев: {len(home_matches)} из 10")
    print(f"Выездные матчи гостей: {len(away_matches)} из 10")

    if len(home_matches) < 5 or len(away_matches) < 5:
        print(
            "\nНедостаточно данных: нужно минимум по 5 "
            "подходящих матчей с каждой стороны. Сигнал не формируем."
        )
        return

    prediction = calculate_prediction(home_matches, away_matches)

    print("\nСРЕДНИЕ ПОКАЗАТЕЛИ И ОЦЕНКА")
    for key, value in prediction.items():
        print(f"{key}: {value}")

    print("\nВЕРОЯТНОСТИ ПО ТОТАЛАМ УГЛОВЫХ (ПУАССОН)")
    expected = prediction["expected_total_corners"]

    for line in [8.5, 9.5, 10.5, 11.5, 12.5]:
        probability = poisson_over_probability(expected, line)
        print(f"ТБ {line}: {probability}%")

    print(
        "\nВажно: это предварительная оценка по Пуассону, "
        "а не откалиброванная вероятность или готовая ставка."
    )


if __name__ == "__main__":
    main()
