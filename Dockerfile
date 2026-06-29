# 1. 選擇基礎映像檔：使用輕量級的 Python 3.10-slim 版本
FROM python:3.12-slim

# 2. 設定工作目錄：容器內的所有操作都會在這個 /app 資料夾底下進行
WORKDIR /app

# 3. 安裝系統依賴：為了確保 psycopg2 等套件能順利編譯，安裝必要的系統工具
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 4. 複製依賴清單並安裝：先複製 requirements.txt 可以善用 Docker 的快取機制，加速後續建置
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 複製專案原始碼：將你專案內的所有檔案複製到容器的 /app 目錄中 (會自動跳過 .dockerignore 裡指定的檔案)
COPY . .

# 6. 設定環境變數：讓 Python 知道 Flask 的主程式是哪一支，並關閉標準輸出的緩衝，方便看 Log
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# 7. 暴露連接埠：宣告容器對外開放 5000 Port
EXPOSE 5000

# 8. 啟動指令：使用 flask run 並綁定 0.0.0.0，確保外部網路可以連進容器內
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]