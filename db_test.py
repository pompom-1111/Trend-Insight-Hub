import psycopg2

# 暫時把這兩行註解掉
# load_dotenv()
# database_url = os.getenv("DATABASE_URL")

# 直接把你的 External Database URL 貼在這裡 (注意前後要有字串引號)
database_url = "postgres://trend_insight_db_user:EdArRS4yJCU1KaAMaSIw1KnU3mx91Qa9@dpg-d8uup47avr4c73fpcvgg-a.singapore-postgres.render.com/trend_insight_db"

try:
    print("正在嘗試硬派連線至資料庫...")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("SELECT NOW();")
    result = cur.fetchone()
    print(f"成功連線！資料庫目前的伺服器時間是: {result[0]}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"連線失敗，發生錯誤: {e}")