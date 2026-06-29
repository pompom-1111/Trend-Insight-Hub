import os
import psycopg2
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

def reset_database():
    """
    強制重置資料庫架構。
    此函式會刪除舊有的 daily_charts 資料表，並建立包含所有必要欄位（含 image_url, song_url）的全新資料表。
    """
    conn = None
    cur = None
    
    try:
        # 建立資料庫連線
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 強制刪除舊表
        cur.execute("DROP TABLE IF EXISTS daily_charts;")
        
        # 建立包含 image_url 與 song_url 的新表結構
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
        
        # 提交變更
        conn.commit()
        print("✅ 資料表已強制重置，現在包含 image_url 和 song_url 欄位！")
        
    except Exception as e:
        print(f"❌ 資料庫重置失敗: {e}")
        if conn:
            conn.rollback()
            
    finally:
        # 確保連線資源被安全釋放
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_database()