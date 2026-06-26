import os
from dotenv import load_dotenv
import psycopg2

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# 定義建立表格的 SQL 語法
CREATE_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS kkbox_daily_charts (
    id SERIAL PRIMARY KEY,
    rank INTEGER NOT NULL,
    song_name VARCHAR(255) NOT NULL,
    artist_name VARCHAR(255) NOT NULL,
    scrape_date DATE DEFAULT CURRENT_DATE
);
"""

def create_table():
    try:
        print("連線至資料庫中...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("正在建立 kkbox_daily_charts 資料表...")
        cur.execute(CREATE_TABLE_QUERY)
        
        # ⚠️ 執行改變資料庫結構的指令，必須 commit 才會正式生效
        conn.commit() 
        
        print("🎉 資料表建立完成！")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    create_table()