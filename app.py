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
        
        query = """
            SELECT platform, rank, song_name, artist_name, image_url, song_url
            FROM daily_charts 
            WHERE scrape_date = CURRENT_DATE 
            ORDER BY platform ASC, rank ASC
        """
        cur.execute(query)
        rows = cur.fetchall()

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
        if cur: cur.close()
        if conn: conn.close()
        
    return songs

@app.route("/")
def index():
    chart_songs = get_charts_data()
    
    def get_platform_score(platform_name):
        try:
            return sum((11 - int(s['rank'])) for s in chart_songs if s['platform'] == platform_name)
        except Exception as e:
            return 0
    
    kkbox_score = get_platform_score('KKBOX')
    yt_score = get_platform_score('YouTube')
    spotify_score = get_platform_score('Spotify')

    # 🌟 新增：字串清洗函數 (Data Cleaning)
    def clean_text(text):
        # 遇到連字號或括號就切斷，只保留最前面的核心歌名，並轉為小寫去除空白
        text = text.split('-')[0].split('(')[0].split('（')[0]
        return text.strip().lower()

    # 跨平台權重演算法
    song_stats = {}
    for s in chart_songs:
        # 🌟 修改：只使用「清洗後的核心歌名」作為鍵值，繞過中英文歌手名稱不一致的問題
        core_song_name = clean_text(s['song_name'])
        unique_key = core_song_name

        try:
            points = 11 - int(s['rank'])
        except:
            points = 0

        if unique_key not in song_stats:
            song_stats[unique_key] = {
                "song_name": s['song_name'], # 畫面依然保留第一次抓到的完整歌名
                "artist_name": s['artist_name'],
                "image_url": s['image_url'],
                "song_url": s['song_url'],
                "total_score": 0,
                "platforms": [] 
            }
        
        song_stats[unique_key]["total_score"] += points
        if s['platform'] not in song_stats[unique_key]["platforms"]:
            song_stats[unique_key]["platforms"].append(s['platform'])

    # 取出前 5 名
    top_integrated_songs = sorted(song_stats.values(), key=lambda x: x['total_score'], reverse=True)[:5]
    
    return render_template("index.html", 
                           songs=chart_songs,
                           kkbox_score=kkbox_score,
                           yt_score=yt_score,
                           spotify_score=spotify_score,
                           top_integrated_songs=top_integrated_songs)

if __name__ == "__main__":
    app.run(debug=True)