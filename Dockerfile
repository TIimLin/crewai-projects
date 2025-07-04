# 步驟 1: 從您已經建立好的基礎映像檔開始
FROM crewai-toolkit

# 步驟 2: 設定工作目錄
WORKDIR /app

# 步驟 3: 將您的專案檔案複製到映像檔中
COPY ./my_first_crew/pyproject.toml /app/my_first_crew/pyproject.toml
COPY ./my_first_crew/src /app/my_first_crew/src/

# 步驟 4: 進入專案目錄，並執行安裝指令
WORKDIR /app/my_first_crew
RUN pip install -e .

# 步驟 5: 設定容器啟動時要執行的預設指令
# 當容器啟動時，它會自動在這個工作目錄下執行 `my_first_crew`
CMD ["my_first_crew"] 