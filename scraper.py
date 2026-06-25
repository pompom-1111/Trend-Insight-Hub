from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

import time

def scrape_kkbox_chart():
    print("啟動系統：準備遙控 Chrome 瀏覽器...")
    
    # 1. 爬蟲禮儀設定：偽裝成正常使用者 (User-Agent)
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # 2. 自動安裝驅動並啟動瀏覽器
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        url = "https://kma.kkbox.com/charts/daily/song?terr=tw&lang=tc"
        print(f"導航至目標網址：{url}")
        driver.get(url)

        # 🔧 調整 1：拉長等待時間，確保 JavaScript 跑完
        print("等待網頁動態載入中 (給它 8 秒鐘)...")
        time.sleep(8) 

        print("開始挖掘排行榜資料...\n")
        
        # 1. 先把所有元素抓回來 (包含隱藏的幽靈)
        raw_song_elements = driver.find_elements(By.CSS_SELECTOR, ".charts-list-song")
        raw_artist_elements = driver.find_elements(By.CSS_SELECTOR, ".charts-list-artist")

        # 2. 裝上過濾器：只保留「文字不是空的」元素 (這招超好用！)
        song_elements = [s for s in raw_song_elements if s.text.strip() != ""]
        artist_elements = [a for a in raw_artist_elements if a.text.strip() != ""]

        print(f"[系統回報] 過濾後，剩下 {len(song_elements)} 首歌曲，{len(artist_elements)} 位歌手")
        print("-" * 30)

        # 3. 再次配對印出前 10 名
        for i, (song, artist) in enumerate(zip(song_elements[:10], artist_elements[:10])):
            rank = i + 1
            song_name = song.text
            artist_name = artist.text
            print(f"第 {rank} 名 | {song_name} - {artist_name}")
            
        print("-" * 30)
        time.sleep(2)

    except Exception as e:
        print(f"發生錯誤：{e}")
    finally:
        # 6. 任務結束，優雅地關閉瀏覽器
        print("任務結束，關閉瀏覽器。")
        driver.quit()

# 執行函式
if __name__ == "__main__":
    scrape_kkbox_chart()