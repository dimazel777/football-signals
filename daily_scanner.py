import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import Counter

BASE = "https://soccer365.ru"
SCHEDULE_URL = BASE + "/online/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

EXCLUDE_WORDS = [
    "кубок",
    "суперкубок",
    "уефа",
    "афк",
    "фифа",
    "лига чемпионов",
    "лига европы",
    "лига конференций",
    "молодеж",
    "молодёж",
    "юнош",
    "резерв",
    "товарищеск",
    "дружеск",
    "u17", "u18", "u19", "u20", "u21", "u23",
]

LEAGUE_WORDS = [
    "серия",
    "дивизион",
    "чемпионат",
    "суперлига",
    "премьер",
    "примера",
    "лига",
]


def get_country(soup):
    for link in soup.select("a[href]"):
        href = link.get("href", "")

        if re.fullmatch(r"/countries/\d+/?", href):
            name = link.get_text(" ", strip=True)

            if name and name.lower() != "страны":
                return name

    return None


def classify_competition(name, title, country):
    if not country:
        return "ИСКЛЮЧИТЬ", "Не найдена конкретная страна"

    text = (name + " " + title).lower()

    for word in EXCLUDE_WORDS:
        if word in text:
            return "ИСКЛЮЧИТЬ", f"Международный или неподходящий турнир: {word}"

    if any(word in text for word in LEAGUE_WORDS):
        return "ПРЕДВАРИТЕЛЬНО ВКЛЮЧИТЬ", "Похоже на национальную лигу"

    return "ПРОВЕРИТЬ", "Тип соревнования не определён"


def main():
    session = requests.Session()
    session.headers.update(HEADERS)

    response = session.get(SCHEDULE_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    blocks = soup.select("div.live_comptt_bd")

    competitions = {}

    for block in blocks:
        header = block.select_one(".block_header")

        if not header:
            continue

        link = header.select_one("a[href*='/competitions/']")

        if not link:
            continue

        competitions[link["href"]] = {
            "name": link.get_text(" ", strip=True),
            "matches": len(block.select(".game_block"))
        }

    print("Найдено соревнований:", len(competitions))

    results = Counter()

    for number, (path, item) in enumerate(competitions.items(), start=1):
        try:
            page = session.get(urljoin(BASE, path), timeout=30)
            page.raise_for_status()

            page_soup = BeautifulSoup(page.text, "html.parser")

            title = (
                page_soup.title.get_text(" ", strip=True)
                if page_soup.title else ""
            )

            country = get_country(page_soup)

            decision, reason = classify_competition(
                item["name"], title, country
            )

            results[decision] += 1

            print("\n" + "=" * 50)
            print(f"{number}/{len(competitions)}")
            print("Турнир:", item["name"])
            print("Страна:", country or "не определена")
            print("Матчей:", item["matches"])
            print("Решение:", decision)
            print("Причина:", reason)

        except requests.RequestException as error:
            print("Ошибка:", item["name"], error)

        time.sleep(0.3)

    print("\nИТОГИ:")
    for decision, count in results.items():
        print(decision, ":", count)


if __name__ == "__main__":
    main()