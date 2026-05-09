from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    # 這是專題的首頁
    title = "Trend-Insight-Hub：跨平台音樂熱度整合系統"
    description = """
    本計畫旨在整合 Spotify、KKBOX 與 YouTube Music 的即時排行榜數據。
    透過動態爬蟲自動化分析全台流行趨勢，為使用者提供一站式的音樂情報儀表板。
    """
    return f"<h1>{title}</h1><p>{description}</p>"

if __name__ == "__main__":
    app.run(debug=True)