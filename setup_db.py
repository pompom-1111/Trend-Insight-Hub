import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
database_url = os.getenv("DATABASE_URL")

def reset_database():
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 強制刪除舊表，並建立包含所有欄位的新表
        cur.execute("DROP TABLE IF EXISTS daily_charts;")
        cur.execute("""
            CREATE TABLE daily_charts (
                id SERIAL PRIMARY KEY,
                platform VARCHAR(50) NOT NULL,
                rank INTEGER NOT NULL,
                song_name VARCHAR(255) NOT NULL,
                artist_name VARCHAR(255) NOT NULL,
                image_url TEXT,
                song_url TEXT,
                scrape_date DATE DEFAULT CURRENT_DATE
            );
        """)
        conn.commit()
        print("✅ 資料表已強制重置，現在包含 image_url 和 song_url 欄位！")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"資料庫重置失敗: {e}")

if __name__ == "__main__":
    reset_database()