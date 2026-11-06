MIN_ODDS = 1.50

CORNER_LINES = [8.5, 9.5, 10.5, 11.5, 12.5]

def select_best_signal(match, model_result):
    """
    Выбирает одну лучшую ставку на тотал угловых за весь матч.

    match — матч из PARI API.
    model_result — результат анализа из soccer365_corners.py.
    """

    qualifying_lines = []

    pari_odds = match.get("currentOdds") or []
    probabilities = model_result.get("probabilities") or {}

    for item in pari_odds:
        outcome_id = item.get("id")
        odds = item.get("value")

        if odds is None:
            continue

        odds = float(odds)

        # Только коэффициенты от 1.50.
        if odds < MIN_ODDS:
            continue

        # Только нужные линии полного матча, исход Over.
        line = {
            737: 8.5,
            739: 9.5,
            741: 10.5,
            743: 11.5,
            745: 12.5,
        }.get(outcome_id)

        if line is None:
            continue

        probability = probabilities.get(line)

        if probability is None:
            probability = probabilities.get(str(line))

        if probability is None:
            continue

        qualifying_lines.append({
            "line": line,
            "odds": odds,
            "probability": float(probability),
            "outcome_id": outcome_id,
        })

    if not qualifying_lines:
        return None

    # Выбираем линию с максимальной прогнозной вероятностью.
    best_signal = max(
        qualifying_lines,
        key=lambda item: item["probability"]
    )

    return best_signal
