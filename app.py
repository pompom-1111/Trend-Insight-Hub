import os
import psycopg2
from flask import Flask, render_template
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# 初始化 Flask 應用程式
app = Flask(__name__)

def get_charts_data():
    """
    從資料庫取得當日的跨平台音樂排行榜資料。
    
    Returns:
        list: 包含每首歌曲排行榜資訊的字典列表。
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
        if cur: 
            cur.close()
        if conn: 
            conn.close()
            
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
        """去除歌名中的連字號或括號，提取核心名稱進行比對"""
        text = text.split('-')[0].split('(')[0].split('（')[0]
        return text.strip().lower()

    # 2. 跨平台權重演算法與資料去重
    song_stats = {}
    for s in chart_songs:
        # 使用清洗後的核心歌名作為唯一識別碼 (Unique Key)
        core_song_name = clean_text(s['song_name'])
        unique_key = core_song_name

        # 計算該首歌曲在目前平台獲得的權重分數
        try:
            points = 11 - int(s['rank'])
        except:
            points = 0

        # 若該歌曲尚未存在於統計字典中，則初始化其資料結構
        if unique_key not in song_stats:
            song_stats[unique_key] = {
                "song_name": s['song_name'],      # 保留第一次抓到的完整歌名以供顯示
                "artist_name": s['artist_name'],  # 保留歌手名稱
                "image_url": s['image_url'],
                "song_url": s['song_url'],
                "total_score": 0,                 # 初始化總分
                "platforms": []                   # 紀錄上榜的平台
            }
        
        # 將分數累加，並紀錄來源平台
        song_stats[unique_key]["total_score"] += points
        if s['platform'] not in song_stats[unique_key]["platforms"]:
            song_stats[unique_key]["platforms"].append(s['platform'])

    # 3. 排序並篩選出全網綜合影響力 Top 5
    # 根據 total_score 由大到小排序
    top_integrated_songs = sorted(song_stats.values(), key=lambda x: x['total_score'], reverse=True)[:5]
    
    # 4. 渲染前端網頁
    return render_template(
        "index.html", 
        songs=chart_songs,
        kkbox_score=kkbox_score,
        yt_score=yt_score,
        spotify_score=spotify_score,
        top_integrated_songs=top_integrated_songs
    )

if __name__ == "__main__":
    app.run(debug=True)