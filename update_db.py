import os
import psycopg2
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

# 定義 SQL 語法：重建資料表結構
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
    """
    資料庫維護腳本：重建 daily_charts 資料表。
    確保資料表欄位與最新架構同步，包含圖片連結與歌曲網址欄位。
    """
    conn = None
    cur = None
    
    try:
        # 建立與資料庫的連線
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 執行重建指令
        cur.execute(CREATE_TABLE_QUERY)
        conn.commit()
        
        print("🎉 資料表 daily_charts 重建完成 (包含 image_url 和 song_url)！")
        
    except Exception as e:
        print(f"❌ 資料庫重建失敗: {e}")
        # 若發生錯誤，進行資料回滾以保護資料庫完整性
        if conn:
            conn.rollback()
    finally:
        # 確保連線資源被安全釋放
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    init_db()