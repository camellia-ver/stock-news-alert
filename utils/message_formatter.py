def format_message(symbol, data):
    meta = data["meta"]
    articles = data["articles"]

    msg = []
    msg.append(f"📊 {symbol}")
    msg.append(f"- 날짜: {meta['date']}")
    msg.append(f"- 변동률: {meta['rate']}%")
    msg.append("")
    msg.append("📰 주요 뉴스")

    for i, a in enumerate(articles[:5], 1):
        msg.append(f"{i}. {a['title']}")
        msg.append(f"   - {a['url']}")

    return "\n".join(msg)