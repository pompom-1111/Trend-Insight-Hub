import os
import time
import re
import requests
import psycopg2
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Selenium 相關套件
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# YouTube Music API 套件
from ytmusicapi import YTMusic

# 載入環境變數
load_dotenv()
database_url = os.getenv("DATABASE_URL")

#資料清洗-以免同歌被誤判成不同首
def clean_song_title(raw_title):
    # 去除小括號及內容，如 "(Official MV)"
    title = re.sub(r'\s*\(.*?\)', '', raw_title)
    # 去除中括號及內容，如 "[Official Video]"
    title = re.sub(r'\s*\[.*?\]', '', title)
    return title.strip()

# ==========================================
# 1. 資料庫寫入模組
# ==========================================
def save_to_db(records):
    """
    將爬蟲取得的排行榜資料寫入 PostgreSQL 資料庫。
    每次寫入前會先清空當日 (CURRENT_DATE) 的舊資料，確保不重複。
    
    參數:
        records (list of tuples): 包含 (platform, rank, song_name, artist_name, image_url, song_url) 的列表。
    """
    conn = None
    cur = None
    try:
        # 🌟 開發階段除錯用：確認資料筆數與樣本
        print(f"DEBUG: 即將寫入的資料筆數: {len(records)}")
        print(f"DEBUG: 第一筆資料樣本: {records[0]}")
        print("\n連線至雲端資料庫準備寫入...")
        
        # 建立資料庫連線
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # 清除當日舊資料，避免重複插入
        cur.execute("DELETE FROM daily_charts WHERE scrape_date = CURRENT_DATE;")
        
        # 🌟 寫入 6 個關鍵欄位 (包含封面圖與歌曲連結)
        insert_query = """
            INSERT INTO daily_charts (platform, rank, song_name, artist_name, image_url, song_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.executemany(insert_query, records)
        conn.commit()
        print(f"🎉 成功清理舊資料，並將 {len(records)} 筆最新資料寫入資料庫！")
        
    except Exception as e:
        print(f"資料庫寫入失敗: {e}")
        # 發生錯誤時進行資料回滾，保護資料庫完整性
        if conn: 
            conn.rollback()
    finally:
        # 確保連線資源被釋放
        if cur: cur.close()
        if conn: conn.close()

# ==========================================
# 2. KKBOX 爬蟲模組
# ==========================================
def scrape_kkbox(driver):
    """
    透過 Selenium 自動化工具抓取 KKBOX 台灣區每日新歌/熱門排行榜。
    
    參數:
        driver (webdriver): 已經初始化的 Selenium Chrome 驅動程式。
    傳回:
        list: 包含 KKBOX 排行榜前 10 名資料的 tuple 列表。
    """
    print("\n[引擎啟動] 開始抓取 KKBOX (UI 模式)...")
    driver.get("https://kma.kkbox.com/charts/daily/song?terr=tw&lang=tc")
    time.sleep(5)  # 等待 JavaScript 渲染網頁內容
    
    records = []
    rows = driver.find_elements(By.CSS_SELECTOR, ".charts-list-row")
    count = 0
    
    for row in rows:
        try:
            song = clean_song_title(row.find_element(By.CSS_SELECTOR, ".charts-list-song").text.strip())
            artist = row.find_element(By.CSS_SELECTOR, ".charts-list-artist").text.strip()
            
            # 抓取圖片，若失敗則使用預設佔位圖
            try:
                image_url = row.find_element(By.TAG_NAME, "img").get_attribute("src")
            except:
                image_url = "https://placehold.co/150x150/00B1D2/white?text=KKBOX"
                
            # 🌟 強制檢查連結，確保不是空值 (None)
            try:
                song_url = row.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                if not song_url: 
                    raise Exception("URL is empty")
            except:
                # 捕捉例外，強制組合搜尋連結作為替代方案
                song_url = f"https://www.kkbox.com/tw/tc/search.php?word={song}+{artist}"

            if song and artist:
                count += 1
                records.append(('KKBOX', count, song, artist, image_url, song_url))
                print(f"KKBOX 第 {count} 名 | {song} - {artist} | 連結確認OK")
            
            # 僅抓取前 10 名
            if count >= 10: 
                break
        except:
            continue
            
    return records

# ==========================================
# 3. YouTube 備用資料模組
# ==========================================
def get_demo_youtube_data():
    """提供 YouTube 的備用測試數據 (主要用於 API 異常時的測試)。"""
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

# ==========================================
# 4. YouTube 爬蟲模組
# ==========================================
def scrape_youtube():
    """
    透過搜尋官方歌單繞過 Charts API 限制，獲取台灣區 YouTube Music 排行榜。
    
    傳回:
        list: 包含 YouTube 排行榜前 10 名資料的 tuple 列表。
    """
    print("\n[引擎啟動] 啟動游擊模式：繞過官方圖表 API，強制搜尋台灣官方歌單...")
    records = []
    try:
        yt = YTMusic(language='zh_TW', location='TW') 
        
        # 🌟 策略轉變：直接搜尋官方的台灣排行榜歌單
        print("👉 正在搜尋官方台灣熱門歌曲清單...")
        search_results = yt.search("台灣百大熱門歌曲", filter="playlists")
        target_playlist_id = None
        
        # 過濾尋找 YouTube Music 官方建立，或標題明確標示台灣的歌單
        for playlist in search_results:
            author = playlist.get('author', '')
            title = playlist.get('title', '')
            if 'YouTube' in author or '台灣' in title or 'Taiwan' in title:
                target_playlist_id = playlist.get('browseId')
                print(f"👉 成功鎖定目標歌單：{title} ({target_playlist_id})")
                break
                
        # 退回機制：若無完美匹配，取搜尋結果第一筆
        if not target_playlist_id and search_results:
            target_playlist_id = search_results[0].get('browseId')
            
        if not target_playlist_id:
            raise Exception("搜尋不到任何台灣排行榜歌單")
            
        print(f"👉 正在解壓縮歌單內容...")
        playlist_data = yt.get_playlist(target_playlist_id)
        top_songs = playlist_data.get('tracks', [])
        
        print(f"✅ 成功提取歌曲，開始擷取...")
        count = 0
        for song in top_songs:
            if count >= 10: break
            
            title = clean_song_title(song.get('title', 'Unknown'))
            
            # 確保歌手名稱能正確從列表中提取並格式化
            artists = song.get('artists', [])
            if isinstance(artists, list):
                artist_name = ", ".join([a.get('name', '') for a in artists if isinstance(a, dict)])
            else:
                artist_name = "Unknown"
                
            # 獲取縮圖或使用預設佔位圖
            thumbnails = song.get('thumbnails', [])
            image_url = thumbnails[-1]['url'] if thumbnails else "https://placehold.co/150x150/FF0000/white?text=YT"
            
            # 組合音樂播放網址
            video_id = song.get('videoId')
            song_url = f"https://music.youtube.com/watch?v={video_id}" if video_id else f"https://music.youtube.com/search?q={title}+{artist_name}"
            
            count += 1
            records.append(('YouTube', count, title, artist_name, image_url, song_url))
            print(f"YouTube 第 {count} 名 | {title} - {artist_name}")
            
    except Exception as e:
        print(f"❌ YouTube 爬蟲發生錯誤: {e}")
        return [] 
        
    return records

# ==========================================
# 5. Spotify 爬蟲與輔助模組
# ==========================================
def fetch_album_art(title, artist):
    """
    透過 iTunes 公開 API 搜尋並取得高畫質的歌曲封面圖。
    
    參數:
        title (str): 歌曲名稱
        artist (str): 歌手名稱
    傳回:
        str: 高解析度(600x600)的圖片 URL 或預設的 Spotify 佔位圖。
    """
    try:
        # 組合並編碼搜尋網址
        term = f"{title} {artist}".replace(" ", "+")
        url = f"https://itunes.apple.com/search?term={term}&entity=song&limit=1"
        response = requests.get(url, timeout=5).json()
        
        if response.get('resultCount', 0) > 0:
            # 取得 100x100 的圖片，並透過字串替換取得 600x600 的高畫質版本
            artwork_url = response['results'][0]['artworkUrl100']
            return artwork_url.replace('100x100bb', '600x600bb')
    except:
        pass
    
    # 若搜尋失敗，返回預設圖片
    return "https://placehold.co/150x150/1DB954/white?text=Spotify"

def scrape_spotify():
    """
    抓取 kworb 統計網的 Spotify 台灣區每日排行榜，並自動補齊圖片與連結。
    
    傳回:
        list: 包含 Spotify 排行榜前 10 名資料的 tuple 列表。
    """
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
        
        # 定位資料表格
        table = soup.find('table', class_='sortable')
        if not table:
            raise Exception("找不到榜單表格，網頁結構可能已改變。")
            
        rows = table.find('tbody').find_all('tr')
        count = 0
        
        # 解析表格列資料
        for row in rows:
            if count >= 10: break
            text_col = row.find('td', class_='text')
            
            if text_col:
                full_text = text_col.text.strip()
                if " - " in full_text:
                    parts = full_text.split(" - ", 1)
                    artist_name = parts[0].strip()
                    title = clean_song_title(parts[1].strip())
                    
                    # 🌟 呼叫輔助函數抓取高畫質封面圖
                    image_url = fetch_album_art(title, artist_name)
                    
                    # 自動生成 Spotify 搜尋連結
                    search_query = f"{title} {artist_name}".replace(" ", "+")
                    song_url = f"https://open.spotify.com/search/{search_query}"
                    
                    count += 1
                    records.append(('Spotify', count, title, artist_name, image_url, song_url))
                    print(f"Spotify 第 {count} 名 | {title} - {artist_name} | 封面抓取成功")
                    
    except Exception as e:
        print(f"❌ Spotify 游擊隊爬蟲失敗: {e}")
        
    return records

# ==========================================
# 主程式執行區塊
# ==========================================
def init_driver():
    """初始化並設定 Selenium 無頭模式 (Headless) 瀏覽器驅動程式。"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

if __name__ == "__main__":
    all_data = []
    
    # 1. 執行 KKBOX 爬蟲 (需要 Selenium)
    driver = init_driver()
    try:
        all_data.extend(scrape_kkbox(driver))
    finally:
        driver.quit() 
    
    # 2. 執行 YouTube 與 Spotify 爬蟲 (輕量級 HTTP/API)
    all_data.extend(scrape_youtube())
    all_data.extend(scrape_spotify())
    
    # 3. 寫入資料庫
    if all_data:
        save_to_db(all_data)
        print("✅ 專案數據全部更新完成！包含專輯封面與歌曲連結！")