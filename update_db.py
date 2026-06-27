import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()
database_url = os.getenv("DATABASE_URL")

# 強制重建表格，確保欄位完整
CREATE_TABLE_QUERY = """
DROP TABLE IF EXISTS daily_charts;
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
"""

def init_db():
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_QUERY)
        conn.commit()
        print("🎉 資料表 daily_charts 重建完成 (包含 image_url 和 song_url)！")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"資料庫重建失敗: {e}")

if __name__ == "__main__":
    init_db()