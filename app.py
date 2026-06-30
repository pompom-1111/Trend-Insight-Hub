import os
import subprocess # 用於在背景執行爬蟲腳本
import psycopg2
from flask import Flask, render_template, request, jsonify # 加入 request, jsonify
from dotenv import load_dotenv
import subprocess
import os

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# 初始化 Flask 應用程式
app = Flask(__name__)

def get_charts_data():
    """
    從資料庫取得當日的跨平台音樂排行榜資料。
    """
    conn = None
    cur = None
    songs = []
    
    try:
        # 建立資料庫連線
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 查詢當日 (CURRENT_DATE) 的所有排行榜資料
        query = """
            SELECT platform, rank, song_name, artist_name, image_url, song_url
            FROM daily_charts 
            WHERE scrape_date = CURRENT_DATE 
            ORDER BY platform ASC, rank ASC
        """
        cur.execute(query)
        rows = cur.fetchall()

        # 將查詢結果整理為字典格式，方便前端讀取
        for row in rows:
            songs.append({
                "platform": row[0],
                "rank": row[1],
                "song_name": row[2],
                "artist_name": row[3],
                "image_url": row[4],
                "song_url": row[5]  
            })
            
    except Exception as e:
        print(f"資料庫讀取錯誤: {e}")
    finally:
        # 確保資料庫連線安全關閉
        if cur: cur.close()
        if conn: conn.close()
            
    return songs

@app.route("/")
def index():
    """
    主頁面路由：計算單一平台總分，並透過資料清洗進行跨平台歌曲權重加總。
    """
    # 1. 取得當日所有歌曲資料
    chart_songs = get_charts_data()
    
    # --- 內部輔助函數：計算單一平台的總權重 ---
    def get_platform_score(platform_name):
        try:
            # 單曲得分公式：11 - 排名
            return sum((11 - int(s['rank'])) for s in chart_songs if s['platform'] == platform_name)
        except Exception as e:
            return 0
    
    # 計算各別平台的分數
    kkbox_score = get_platform_score('KKBOX')
    yt_score = get_platform_score('YouTube')
    spotify_score = get_platform_score('Spotify')

    # --- 內部輔助函數：資料清洗 (Data Cleaning) ---
    def clean_text(text):
        """去除歌名中的括號與分隔符號，提取核心名稱進行比對"""
        text = text.split('(')[0].split('（')[0].split('[')[0].split('【')[0]
        if " - " in text:
            text = text.split(" - ")[0]
        return text.strip().lower()

    # 2. 跨平台權重演算法與資料去重
    song_stats = {}
    for s in chart_songs:
        core_song_name = clean_text(s['song_name'])
        unique_key = core_song_name

        try:
            points = 11 - int(s['rank'])
        except:
            points = 0

        if unique_key not in song_stats:
            song_stats[unique_key] = {
                "song_name": s['song_name'],
                "artist_name": s['artist_name'],
                "image_url": s['image_url'],
                "song_url": s['song_url'],
                "total_score": 0,
                "platforms": []
            }
        
        song_stats[unique_key]["total_score"] += points
        if s['platform'] not in song_stats[unique_key]["platforms"]:
            song_stats[unique_key]["platforms"].append(s['platform'])

    # 3. 排序並篩選出全網綜合影響力 Top 5
    top_integrated_songs = sorted(song_stats.values(), key=lambda x: x['total_score'], reverse=True)[:5]
    
    return render_template(
        "index.html", 
        songs=chart_songs,
        kkbox_score=kkbox_score,
        yt_score=yt_score,
        spotify_score=spotify_score,
        top_integrated_songs=top_integrated_songs
    )

# --- 新增的爬蟲觸發路由 ---
# 修改 trigger_scraper 函式中的密碼檢查邏輯
@app.route('/api/run-scraper')
def trigger_scraper():
    # 從環境變數讀取密碼
    secret_key = request.args.get('key')
    required_key = os.getenv("SCRAPER_SECRET")
    
    # 加入防呆檢查：如果環境變數沒設，回傳錯誤
    if not required_key:
        return jsonify({"status": "error", "message": "Server configuration error"}), 500

    if secret_key != required_key:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    try:
        # 修改這一行，將 output 和 error 都導向 DEVNULL，不要讓日誌影響到請求
        subprocess.Popen(
            ["python", "scraper.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return jsonify({"status": "success", "message": "Scraper started"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # 在 Render 上部署時，確保 debug 為 False
    app.run(debug=False)