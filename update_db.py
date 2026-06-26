import os
from dotenv import load_dotenv
import psycopg2

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# 定義建立新表格的 SQL 語法
# 我們將表名改為通用的 daily_charts，並新增 platform 欄位
CREATE_NEW_TABLE_QUERY = """
CREATE TABLE IF NOT EXISTS daily_charts (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,   -- 新增：用來紀錄是 'KKBOX' 還是 'YouTube'
    rank INTEGER NOT NULL,
    song_name VARCHAR(255) NOT NULL,
    artist_name VARCHAR(255) NOT NULL,
    scrape_date DATE DEFAULT CURRENT_DATE
);
"""

def upgrade_database():
    try:
        print("連線至雲端資料庫中...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        print("正在建立通用版排行榜表格 (daily_charts)...")
        cur.execute(CREATE_NEW_TABLE_QUERY)
        conn.commit() 
        
        print("🎉 新資料表建立完成！我們現在有能力容納多個平台的資料了。")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"發生錯誤: {e}")

if __name__ == "__main__":
    upgrade_database()