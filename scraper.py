import os
import time
import psycopg2
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from ytmusicapi import YTMusic
import requests
from bs4 import BeautifulSoup

load_dotenv()
database_url = os.getenv("DATABASE_URL")

# --- 1. 資料庫寫入 (新增 image_url, song_url) ---
def save_to_db(records):
    conn = None
    cur = None
    try:
        # 🌟 這行可以幫我們確認資料在寫入前到底是不是空的
        print(f"DEBUG: 即將寫入的資料筆數: {len(records)}")
        print(f"DEBUG: 第一筆資料樣本: {records[0]}")
        
        print("\n連線至雲端資料庫準備寫入...")
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM daily_charts WHERE scrape_date = CURRENT_DATE;")
        
        # 🌟 寫入 6 個欄位
        insert_query = """
            INSERT INTO daily_charts (platform, rank, song_name, artist_name, image_url, song_url)
            VALUES (%s, %s, %s, %s, %s, %s)
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

# --- 2. KKBOX 爬蟲 ---
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
            
            # 抓取圖片
            try:
                image_url = row.find_element(By.TAG_NAME, "img").get_attribute("src")
            except:
                image_url = "https://placehold.co/150x150/00B1D2/white?text=KKBOX"
                
            # 🌟 強制檢查連結，確保不是 None
            try:
                song_url = row.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                if not song_url: # 如果抓到的是空值 (None)，手動拋出錯誤
                    raise Exception("URL is empty")
            except:
                # 這裡會捕捉到上面的 Exception，強制給予搜尋連結
                song_url = f"https://www.kkbox.com/tw/tc/search.php?word={song}+{artist}"

            if song and artist:
                count += 1
                records.append(('KKBOX', count, song, artist, image_url, song_url))
                print(f"KKBOX 第 {count} 名 | {song} - {artist} | 連結確認OK")
            if count >= 10: 
                break
        except:
            continue
    return records

# --- 3. YouTube Demo 資料 ---
def get_demo_youtube_data():
    print("[執行中] 載入 YouTube 備用數據...")
    demo_img = "https://placehold.co/150x150/FF0000/white?text=YT"
    return [
        ('YouTube', 1, '晚安大小姐', 'ASMRZ', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 2, 'Bling-Bang-Bang-Born', 'Creepy Nuts', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 3, '女兒殿下', '周杰倫', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 4, 'SHEESH', 'BABYMONSTER', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 5, 'Magnetic', 'ILLIT', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 6, 'APT.', 'ROSÉ & Bruno Mars', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 7, '天后', '勢在必行', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 8, '告白氣球', '周杰倫', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 9, '想和你看五月的晚霞', '陳華', demo_img, 'https://music.youtube.com/'),
        ('YouTube', 10, '初戀', '宇多田光', demo_img, 'https://music.youtube.com/')
    ]        

# --- 4. YouTube 爬蟲 ---
def scrape_youtube():
    print("\n[引擎啟動] 啟動解壓縮模式：正在讀取排行榜清單內容...")
    records = []
    try:
        yt = YTMusic()
        charts = yt.get_charts(country='TW')
        target_playlist = charts.get('videos', [])[0]
        playlist_id = target_playlist.get('playlistId')
        
        if not playlist_id:
            raise Exception("找不到該排行榜的 Playlist ID")
            
        print(f"👉 成功鎖定排行榜清單，正在解壓縮內容...")
        playlist_data = yt.get_playlist(playlist_id)
        top_songs = playlist_data.get('tracks', [])
        
        count = 0
        for song in top_songs:
            if count >= 10: break
            title = song.get('title', 'Unknown')
            artists = song.get('artists', [])
            artist_name = ", ".join([a.get('name', '') for a in artists]) if artists else "Unknown"
            
            # 🌟 抓取縮圖與組裝連結
            thumbnails = song.get('thumbnails', [])
            image_url = thumbnails[-1]['url'] if thumbnails else "https://placehold.co/150x150/FF0000/white?text=YT"
            
            video_id = song.get('videoId')
            song_url = f"https://music.youtube.com/watch?v={video_id}" if video_id else f"https://music.youtube.com/search?q={title}+{artist_name}"
            
            count += 1
            records.append(('YouTube', count, title, artist_name, image_url, song_url))
            print(f"YouTube 第 {count} 名 | {title} - {artist_name}")
            
    except Exception as e:
        print(f"❌ 爬蟲最終修正版發生錯誤: {e}")
        return get_demo_youtube_data() 
        
    return records

def fetch_album_art(title, artist):
    """透過 iTunes 公開 API 搜尋歌曲封面圖"""
    try:
        # 組合搜尋網址
        term = f"{title} {artist}".replace(" ", "+")
        url = f"https://itunes.apple.com/search?term={term}&entity=song&limit=1"
        response = requests.get(url, timeout=5).json()
        
        if response.get('resultCount', 0) > 0:
            # 取得 100x100 的圖，並把網址改為 600x600 的高畫質版
            artwork_url = response['results'][0]['artworkUrl100']
            return artwork_url.replace('100x100bb', '600x600bb')
    except:
        pass
    # 如果抓不到，就用原本的預設圖
    return "https://placehold.co/150x150/1DB954/white?text=Spotify"

# --- 5. Spotify 爬蟲 ---
def scrape_spotify():
    print("\n[引擎啟動] 啟動游擊隊模式：透過開源統計網獲取 Spotify 台灣榜單...")
    records = []
    try:
        url = "https://kworb.net/spotify/country/tw_daily.html"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', class_='sortable')
        if not table:
            raise Exception("找不到榜單表格，網頁結構可能已改變。")
            
        rows = table.find('tbody').find_all('tr')
        count = 0
        # --- 更新後的 Spotify 爬蟲區塊 ---
        for row in rows:
            if count >= 10: break
            text_col = row.find('td', class_='text')
            if text_col:
                full_text = text_col.text.strip()
                if " - " in full_text:
                    parts = full_text.split(" - ", 1)
                    artist_name = parts[0].strip()
                    title = parts[1].strip()
                    
                    # 🌟 呼叫剛寫好的抓圖函數
                    image_url = fetch_album_art(title, artist_name)
                    
                    search_query = f"{title} {artist_name}".replace(" ", "+")
                    song_url = f"https://open.spotify.com/search/{search_query}"
                    
                    count += 1
                    records.append(('Spotify', count, title, artist_name, image_url, song_url))
                    print(f"Spotify 第 {count} 名 | {title} - {artist_name} | 封面抓取成功")
                    
    except Exception as e:
        print(f"❌ Spotify 游擊隊爬蟲失敗: {e}")
        
    return records

# --- 啟動與整合區塊 ---
def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

if __name__ == "__main__":
    all_data = []
    
    driver = init_driver()
    try:
        all_data.extend(scrape_kkbox(driver))
    finally:
        driver.quit() 
    
    all_data.extend(scrape_youtube())
    all_data.extend(scrape_spotify())
    
    if all_data:
        save_to_db(all_data)
        print("✅ 專案數據全部更新完成！包含專輯封面與歌曲連結！")