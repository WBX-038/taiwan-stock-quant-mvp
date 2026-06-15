def rating_from_score(score: float | None) -> str:
    if score is None:
        return "資料不足"
    if score >= 85:
        return "強力買進"
    if score >= 70:
        return "買進"
    if score >= 50:
        return "持有"
    if score >= 30:
        return "賣出"
    return "強力賣出"
