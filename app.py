import os
from flask import Flask, render_template
import psycopg2
from dotenv import load_dotenv

load_dotenv()
database_url = os.getenv("DATABASE_URL")
app = Flask(__name__)

def get_charts_data():
    conn = None
    cur = None
    songs = []
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 🌟 關鍵修正 1：SQL 查詢加入 image_url 與 song_url
        query = """
            SELECT platform, rank, song_name, artist_name, image_url, song_url
            FROM daily_charts 
            WHERE scrape_date = CURRENT_DATE 
            ORDER BY platform ASC, rank ASC
        """
        
        cur.execute(query)
        rows = cur.fetchall()

        # 🌟 關鍵修正 2：把抓到的這兩個新資料，一起打包給前端
        for row in rows:
            songs.append({
                "platform": row[0],
                "rank": row[1],
                "song_name": row[2],
                "artist_name": row[3],
                "image_url": row[4], # 抓取圖片網址
                "song_url": row[5]   # 抓取歌曲連結
            })
            
    except Exception as e:
        print(f"資料庫讀取錯誤: {e}")
    finally:
        if cur: cur.close()
        if conn: conn.close()
        
    return songs

@app.route("/")
def index():
    chart_songs = get_charts_data()
    return render_template("index.html", songs=chart_songs)

if __name__ == "__main__":
    app.run(debug=True)