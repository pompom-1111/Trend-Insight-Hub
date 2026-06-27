import os
from dotenv import load_dotenv
import psycopg2

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# 定義重建表格的 SQL 語法
# ⚠️ 注意：為了確保新的欄位能正確套用，這裡會先刪除舊表再重建
RESET_TABLE_QUERY = """
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

def create_table():
    conn = None
    cur = None
    try:
        print("連線至資料庫中...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("正在重建 daily_charts 資料表並新增圖片與連結欄位...")
        cur.execute(RESET_TABLE_QUERY)
        
        # ⚠️ 執行改變資料庫結構的指令，必須 commit 才會正式生效
        conn.commit() 
        
        print("🎉 資料表重建完成！現在支援三平台與封面連結了！")
        
    except Exception as e:
        print(f"發生錯誤: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table()