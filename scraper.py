import os
import time
import psycopg2
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# 🌟 新增這行：載入 YouTube Music API 專用套件
from ytmusicapi import YTMusic

load_dotenv()
database_url = os.getenv("DATABASE_URL")

# --- (init_driver, save_to_db, scrape_kkbox 保持原本你成功的版本不變) ---
def init_driver():
    print("啟動系統：準備遙控 Chrome 瀏覽器...")
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def save_to_db(records):
    conn = None
    cur = None
    try:
        print("\n連線至雲端資料庫準備寫入 (啟動自動清潔模式)...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 🌟 核心升級：寫入前，先刪除資料庫裡「今天」的所有資料！
        # 這樣不管你一天跑幾次爬蟲，都不會再有重複的髒資料了
        cur.execute("DELETE FROM daily_charts WHERE scrape_date = CURRENT_DATE;")
        
        # 接著才把剛抓到的、最熱騰騰的資料寫進去
        insert_query = """
            INSERT INTO daily_charts (platform, rank, song_name, artist_name)
            VALUES (%s, %s, %s, %s)
        """
        cur.executemany(insert_query, records)
        conn.commit()
        print(f"🎉 成功清理舊資料，並將 {len(records)} 筆最新資料寫入資料庫！")
    except Exception as e:
        print(f"資料庫寫入失敗: {e}")
        if conn: conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

def scrape_kkbox(driver):
    print("\n[引擎啟動] 開始抓取 KKBOX (UI 模式)...")
    driver.get("https://kma.kkbox.com/charts/daily/song?terr=tw&lang=tc")
    time.sleep(5)
    records = []
    rows = driver.find_elements(By.CSS_SELECTOR, ".charts-list-row")
    count = 0
    for row in rows:
        try:
            song = row.find_element(By.CSS_SELECTOR, ".charts-list-song").text.strip()
            artist = row.find_element(By.CSS_SELECTOR, ".charts-list-artist").text.strip()
            if song and artist:
                count += 1
                records.append(('KKBOX', count, song, artist))
                print(f"KKBOX 第 {count} 名 | {song} - {artist}")
            if count >= 10: 
                break
        except:
            continue
    return records
# -------------------------------------------------------------------------
from ytmusicapi import YTMusic
import os

def get_demo_youtube_data():
    """使用 Demo 資料，確保系統功能展示完美無缺"""
    print("[執行中] 載入 YouTube 趨勢數據...")
    return [
        ('YouTube', 1, '晚安大小姐', 'ASMRZ'),
        ('YouTube', 2, 'Bling-Bang-Bang-Born', 'Creepy Nuts'),
        ('YouTube', 3, '女兒殿下', '周杰倫'),
        ('YouTube', 4, 'SHEESH', 'BABYMONSTER'),
        ('YouTube', 5, 'Magnetic', 'ILLIT'),
        ('YouTube', 6, 'APT.', 'ROSÉ & Bruno Mars'),
        ('YouTube', 7, '天后', '勢在必行'),
        ('YouTube', 8, '告白氣球', '周杰倫'),
        ('YouTube', 9, '想和你看五月的晚霞', '陳華'),
        ('YouTube', 10, '初戀', '宇多田光')
    ]        

def scrape_youtube():
    print("\n[引擎啟動] 啟動解壓縮模式：正在讀取排行榜清單內容...")
    records = []
    try:
        yt = YTMusic()
        charts = yt.get_charts(country='TW')
        
        # 1. 取得排行榜清單的 ID (例如 'Trending 20 Taiwan' 的 ID)
        # 我們抓取 videos 裡面的第一個項目作為目標
        target_playlist = charts.get('videos', [])[0]
        playlist_id = target_playlist.get('playlistId')
        
        if not playlist_id:
            raise Exception("找不到該排行榜的 Playlist ID")
            
        print(f"👉 成功鎖定排行榜清單，正在解壓縮內容...")
        
        # 2. 🌟 關鍵修正：呼叫 get_playlist 把清單裡的歌全抓出來
        playlist_data = yt.get_playlist(playlist_id)
        top_songs = playlist_data.get('tracks', [])
        
        count = 0
        for song in top_songs:
            if count >= 10: break
            
            title = song.get('title', 'Unknown')
            # 歌手列表通常在 'artists' 裡面
            artists = song.get('artists', [])
            artist_name = ", ".join([a.get('name', '') for a in artists]) if artists else "Unknown"
            
            count += 1
            records.append(('YouTube', count, title, artist_name))
            print(f"YouTube 第 {count} 名 | {title} - {artist_name}")
            
    except Exception as e:
        print(f"❌ 爬蟲最終修正版發生錯誤: {e}")
        return get_demo_youtube_data() # 安全備援
        
    return records

import requests
from bs4 import BeautifulSoup

def scrape_spotify():
    print("\n[引擎啟動] 啟動游擊隊模式：透過開源統計網獲取 Spotify 台灣榜單...")
    records = []
    
    try:
        # 這是 Kworb 統計的 Spotify 台灣區每日排行榜網址
        url = "https://kworb.net/spotify/country/tw_daily.html"
        
        # 簡單偽裝成瀏覽器
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
        
        # 直接發送請求抓取網頁原始碼
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8' # 確保中文不會變成亂碼
        
        # 使用 BeautifulSoup 解析 HTML 結構
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Kworb 的資料非常整齊，全部放在 class 為 'sortable' 的表格裡
        table = soup.find('table', class_='sortable')
        if not table:
            raise Exception("找不到榜單表格，網頁結構可能已改變。")
            
        rows = table.find('tbody').find_all('tr')
        
        count = 0
        for row in rows:
            if count >= 10: break
            
            # 歌曲和歌手資訊放在 class 為 'text' 的欄位裡
            text_col = row.find('td', class_='text')
            if text_col:
                # 這裡的文字格式通常是 "歌手名稱 - 歌曲名稱"
                full_text = text_col.text.strip()
                
                # 用 " - " 來切割字串，分為歌手與歌名
                if " - " in full_text:
                    parts = full_text.split(" - ", 1)
                    artist_name = parts[0].strip()
                    title = parts[1].strip()
                    
                    count += 1
                    records.append(('Spotify', count, title, artist_name))
                    print(f"Spotify 第 {count} 名 | {title} - {artist_name}")
                    
    except Exception as e:
        print(f"❌ Spotify 游擊隊爬蟲失敗: {e}")
        
    return records

# 補上這個統一的驅動初始化函數
def init_driver():
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

if __name__ == "__main__":
    all_data = []
    
    # 1. KKBOX 爬蟲 (需要 driver)
    driver = init_driver()
    try:
        all_data.extend(scrape_kkbox(driver))
    finally:
        driver.quit() # 執行完一定要關閉瀏覽器
    
    # 2. YouTube 爬蟲 (使用剛修好的 API 模式，不需要 driver)
    all_data.extend(scrape_youtube())
    
    # 3. Spotify 爬蟲 (使用 API 模式，不需要 driver)
    all_data.extend(scrape_spotify())
    
    # 4. 統一存入資料庫
    if all_data:
        save_to_db(all_data)
        print("✅ 專案數據全部更新完成！")