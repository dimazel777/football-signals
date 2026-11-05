import re
import time
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin

import daily_scanner as ds

SCHEDULE_URL = "https://soccer365.ru/online/"

def is_excluded_match(match_name):
    """Исключает молодёжные и резервные команды."""

    name = match_name.lower()

    excluded_words = [
        "молодёж",
        "молодеж",
        "юнош",
        "резерв",
        "резервист",
        "youth",
        "junior",
        "under-",
        "u17",
        "u18",
        "u19",
        "u20",
        "u21",
        "u23",
    ]

    for word in excluded_words:
        if word in name:
            return True, f"Молодёжная или резервная команда: {word}"

    teams = re.split(r"\s[-–—]\s", name)

    for team in teams:
        team = team.strip()

        if re.search(r"(?:\s|^)(?:2|ii)$", team):
            return True, "Вторая команда"

    return False, ""

def is_excluded_competition(name, title):
    """Дополнительная защита от молодёжных соревнований."""

    text = f"{name} {title}".lower()

    excluded_words = [
        "мфл",
        "молодёж",
        "молодеж",
        "юнош",
        "резерв",
        "youth",
        "junior",
        "u17",
        "u18",
        "u19",
        "u20",
        "u21",
        "u23",
    ]

    for word in excluded_words:
        if word in text:
            return True

    return False

def main():
    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        )
    })

    print("Загружаю расписание Soccer365...")

    try:
        response = session.get(
            SCHEDULE_URL,
            timeout=30
        )
        response.raise_for_status()

    except requests.RequestException as error:
        print(f"Ошибка загрузки расписания: {error}")
        return

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    competition_blocks = soup.select("div.live_comptt_bd")

    print(f"Найдено блоков соревнований: {len(competition_blocks)}")

    matches = []
    seen_urls = set()

    included_competitions = 0
    excluded_competitions = 0
    excluded_matches = 0
    errors = 0

    for block in competition_blocks:

        header = block.select_one(".block_header")

        if not header:
            continue

        comp_link = header.select_one(
            "a[href*='/competitions/']"
        )

        if not comp_link:
            continue

        name = comp_link.get_text(
            " ",
            strip=True
        )

        path = comp_link.get("href")

        if not path:
            continue

        try:
            page = session.get(
                urljoin(ds.BASE, path),
                timeout=30
            )
            page.raise_for_status()

            page_soup = BeautifulSoup(
                page.text,
                "html.parser"
            )

            title = (
                page_soup.title.get_text(" ", strip=True)
                if page_soup.title
                else ""
            )

            country = ds.get_country(page_soup)

            decision, reason = ds.classify_competition(
                name,
                title,
                country
            )

            if decision != "ПРЕДВАРИТЕЛЬНО ВКЛЮЧИТЬ":
                excluded_competitions += 1
                continue

            if is_excluded_competition(name, title):
                excluded_competitions += 1
                continue

            included_competitions += 1

            for game in block.select(".game_block"):

                link = game.select_one("a.game_link")
                status = game.select_one(".status")

                if not link or not status:
                    continue

                kickoff = status.get_text(
                    " ",
                    strip=True
                )

                # Берём только матчи с обычным временем начала.
                # Завершённые и ренесённые матчи пропускаем.
                if not re.fullmatch(
                    r"\d{1,2}:\d{2}",
                    kickoff
                ):
                    continue

                match_name = link.get_text(
                    " ",
                    strip=True
                )

                excluded, exclusion_reason = is_excluded_match(
                    match_name
                )

                if excluded:
                    excluded_matches += 1
                    continue

                match_path = link.get("href")

                if not match_path:
                    continue

                match_url = urljoin(
                    ds.BASE,
                    match_path
                )

                if match_url in seen_urls:
                    continue

                seen_urls.add(match_url)

                matches.append({
                    "competition": name,
                    "country": country,
                    "kickoff": kickoff,
                    "match": match_name,
                    "url": match_url,
                })

            time.sleep(0.3)

        except requests.RequestException as error:
            errors += 1
            print(f"Ошибка соревнования {name}: {error}")
            continue

        except Exception as error:
            errors += 1
            print(f"Не удалось обработать {name}: {error}")
            continue

    matches.sort(
        key=lambda item: item["kickoff"]
    )

    print("\n" + "=" * 55)
    print("РЕЗУЛЬТАТ СБОРА РАСПИСАНИЯ")
    print("=" * 55)

    print(f"Включено соревнований: {included_competitions}")
    print(f"Исключено соревнований: {excluded_competitions}")
    print(f"Исключено молодёжных/резервных матчей: {excluded_matches}")
    print(f"Ошибок обработки: {errors}")
    print(f"Найдено подходящих матчей: {len(matches)}")

    print("\nСПИСОК МАТЧЕЙ")
    print("-" * 55)

    for number, match in enumerate(matches, start=1):

        print(
            f"\n{number}. {match['kickoff']} | "
            f"{match['country']}"
        )

        print(f"   Турнир: {match['competition']}")
        print(f"   Матч: {match['match']}")
        print(f"   Ссылка: {match['url']}")

    print("\nСбор расписания завершён.")
    return matches

if __name__ == "__main__":
    main()
