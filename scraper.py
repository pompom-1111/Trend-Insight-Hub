import os
import time
import psycopg2
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# 1. 載入環境變數 (拿取資料庫鑰匙)
load_dotenv()
database_url = os.getenv("DATABASE_URL")

def scrape_kkbox_chart():
    print("啟動系統：準備遙控 Chrome 瀏覽器...")
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 準備資料庫連線的變數
    conn = None
    cur = None

    try:
        url = "https://kma.kkbox.com/charts/daily/song?terr=tw&lang=tc"
        print(f"導航至目標網址: {url}")
        driver.get(url)
        
        print("等待網頁動態載入中 (給它 8 秒鐘)...")
        time.sleep(8)
        
        print("開始挖掘排行榜資料...\n")
        
        raw_song_elements = driver.find_elements(By.CSS_SELECTOR, ".charts-list-song")
        raw_artist_elements = driver.find_elements(By.CSS_SELECTOR, ".charts-list-artist")
        
        song_elements = [s for s in raw_song_elements if s.text.strip() != ""]
        artist_elements = [a for a in raw_artist_elements if a.text.strip() != ""]
        
        print(f"[系統回報] 過濾後，剩下 {len(song_elements)} 首歌曲，{len(artist_elements)} 位歌手")
        print("-" * 30)

        # 2. 開啟資料庫連線
        print("連線至雲端資料庫準備寫入...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 準備寫入資料的 SQL 語法
        insert_query = """
            INSERT INTO kkbox_daily_charts (rank, song_name, artist_name)
            VALUES (%s, %s, %s)
        """
        
        # 3. 處理前 10 名並寫入資料庫
        for i, (song, artist) in enumerate(zip(song_elements[:10], artist_elements[:10])):
            rank = i + 1
            song_name = song.text.strip()
            artist_name = artist.text.strip()
            
            print(f"第 {rank} 名 | {song_name} - {artist_name}")
            
            # 執行寫入動作
            cur.execute(insert_query, (rank, song_name, artist_name))
        
        # 4. 確定資料都塞進去後，按下「確認送出」(commit)
        conn.commit()
        print("\n🎉 成功將前 10 名資料寫入 Render PostgreSQL 資料庫！")

    except Exception as e:
        print(f"發生錯誤: {e}")
        if conn is not None:
            conn.rollback()  # 如果發生錯誤，把這波操作退回，保護資料庫
    finally:
        # 5. 任務結束，優雅地關閉所有資源
        print("任務結束，關閉瀏覽器與資料庫連線。")
        driver.quit()
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    scrape_kkbox_chart()