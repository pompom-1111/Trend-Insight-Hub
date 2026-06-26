import os
from flask import Flask, render_template
import psycopg2
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

app = Flask(__name__)

def get_charts_data():
    """從雲端資料庫撈取最新的前 10 名排行榜資料"""
    conn = None
    cur = None
    songs = []
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 撈取當天前 10 名的歌曲
        query = """
            SELECT rank, song_name, artist_name, scrape_date 
            FROM kkbox_daily_charts 
            ORDER BY scrape_date DESC, rank ASC 
            LIMIT 10
        """
        cur.execute(query)
        rows = cur.fetchall()
        
        # 將資料包裝成字典格式，方便網頁讀取
        for row in rows:
            songs.append({
                "rank": row[0],
                "song_name": row[1],
                "artist_name": row[2],
                "scrape_date": row[3]
            })
            
    except Exception as e:
        print(f"資料庫讀取失敗: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
        
    return songs

@app.route("/")
def index():
    # 1. 呼叫資料庫函式拿取資料
    chart_songs = get_charts_data()
    
    # 2. 將資料送進 index.html 模板進行渲染
    return render_template("index.html", songs=chart_songs)

if __name__ == "__main__":
    # 啟動本地測試伺服器，開啟 debug 模式方便排錯
    app.run(debug=True)