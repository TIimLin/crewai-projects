# AI Crew 專案開發標準指南 

本文件將指導您採用一個高效、可重現的標準化流程，來開發任何 `crewAI` 專案。我們將首先建立一個通用的「工具箱」，然後利用它來快速生成、客製化並執行我們的 AI 旅遊規劃師專案。

---

## Part 1: 【一次性設定】建立您的 CrewAI 工具箱

這一步我們將建立一個包含 Python、CrewAI 及所有官方工具的 Docker 映像檔。這個映像檔是您未來所有 CrewAI 專案的基礎，**只需要建立一次**。

1.  **建立 Toolkit 的 Dockerfile**
    在您的工作區根目錄（例如 `crewai-projects/`）下，建立一個名為 `Dockerfile.toolkit` 的檔案。

2.  **填入以下內容**：
    此檔案定義了一個包含最新 `crewai[tools]` 套件的基礎環境。

    ```dockerfile
    # Dockerfile.toolkit

    # 使用官方 Python 3.11 Slim 作為基礎映像檔
    FROM python:3.11-slim

    # 安裝 git，某些 Python 套件在安裝時需要
    RUN apt-get update && apt-get install -y git

    # 安裝 crewai 及其所有可選工具 (Serper, ScrapeWebsiteTool, etc.)
    RUN pip install 'crewai[tools]'

    # 設定工作目錄
    WORKDIR /app
    ```

3.  **建置工具箱映像檔**
    在終端機中，執行以下指令來建置名為 `crewai-toolkit` 的映像檔。

    ```bash
    docker build -t crewai-toolkit -f Dockerfile.toolkit .
    ```
    建置完成後，`crewai-toolkit` 就會存在於您電腦的 Docker 環境中，隨時可以取用。

---

## Part 2: 【專案開發流程】以旅遊規劃師為例

現在我們將使用上面建立的 `crewai-toolkit` 來從零到有地建立我們的 AI 旅遊規劃師。

### 步驟 1: 自動建立專案骨架

首先，請確保您的終端機位於您希望存放所有 AI 專案的資料夾中（例如 `crewai-projects/`）。`crewAI` 會在您目前所在的位置建立新的專案資料夾。未來若要建立其他專案，只需在不同的位置重複此步驟即可。

1.  **啟動工具箱容器**
    在終端機中，執行以下指令。這會啟動一個暫時的容器，並將您當前的主機目錄掛載進去，讓您可以在裡面執行 `crewai` 指令。

    ```bash
    # -it: 讓我們可以與容器互動
    # --rm: 容器結束後自動刪除
    # -v "$(pwd):/app": 將當前目錄掛載到容器的 /app
    docker run -it --rm -v "$(pwd):/app" crewai-toolkit /bin/bash
    ```

2.  **執行建立指令**
    進入容器的命令列後，執行 `crewai` 的建立指令：

    ```bash
    # crewai create crew <您的專案名稱>
    crewai create crew my_travel_planner
    ```
    *   `crewAI` 會詢問您偏好的 LLM (OpenAI/Azure/Gemini)，請依指示輸入數字。
    *   它會自動建立一個名為 `my_travel_planner` 的資料夾，裡面包含了所有必要的檔案，包括 `agents.yaml`, `tasks.yaml`, `crew.py`, `main.py`, `pyproject.toml` 以及一個 `.env` 檔案範本。

3.  **退出容器**
    專案建立完成後，輸入 `exit` 並按下 Enter，即可退出並關閉容器。

    ```bash
    exit
    ```
    現在，您的主機目錄下已經有了一個全新的 `my_travel_planner` 專案。

### 步驟 2: 客製化您的旅遊 Crew

現在，我們需要修改自動生成的檔案，將它從一個通用模板變成我們的專屬旅遊規劃師。

1.  **填寫 API 金鑰**
    *   **檔案**：`my_travel_planner/.env`
    *   **操作**：打開這個檔案，將您申請的 `SERPER_API_KEY` 和您選擇的 LLM 的 `API_KEY` 填入其中。
        ```ini
        # my_travel_planner/.env
        SERPER_API_KEY="your_serper_api_key"
        OPENAI_API_KEY="your_openai_or_gemini_api_key"
        ```

2.  **定義 Agents (`agents.yaml`)**
    *   **檔案**：`my_travel_planner/src/my_travel_planner/config/agents.yaml`
    *   **操作**：用以下內容覆蓋整個檔案。
        ```yaml
        expert_travel_agent:
          role: "資深旅行規劃師"
          goal: "根據使用者需求，尋找最優質的航班與飯店選項。"
          backstory: "你是一位經驗豐富的旅行規劃專家，精通全球航班與訂房系統，總能為客戶找到性價比最高的選擇。"
          tools:
            - "serper_dev_tool"
          allow_delegation: false
          verbose: true

        local_expert:
          role: "在地文化導遊"
          goal: "為旅客規劃深入且真實的在地行程，發掘隱藏的景點與美食。"
          backstory: "你是一位在 {destination} 土生土長的在地達人，對這裡的歷史文化、街頭小吃、私房景點瞭若指掌。你的推薦總能讓旅客體驗到最道地的風情。"
          tools:
            - "serper_dev_tool"
            - "scrape_website_tool"
          allow_delegation: false
          verbose: true

        travel_concierge:
          role: "行程整合管家"
          goal: "將所有零散的旅遊資訊，彙整成一份清晰、精美且完整的旅遊手冊，並以檔案形式交付。"
          backstory: "你是一位注重細節、追求完美的行程管家。你的任務是確保最終產出的旅遊手冊不僅內容完整，格式也要優雅易讀，讓旅客一目了然。"
          tools:
            - "file_writer_tool"
          allow_delegation: false
          verbose: true
        ```

3.  **定義 Tasks (`tasks.yaml`)**
    *   **檔案**：`my_travel_planner/src/my_travel_planner/config/tasks.yaml`
    *   **操作**：用以下內容覆蓋整個檔案。
        ```yaml
        identify_flights_and_hotels:
          description: >-
            為一趟前往 {destination} 的 {duration} 旅遊，搜尋最佳的航班與飯店。
            旅客的興趣是：{interests}。出發日期為 {start_date}，返回日期為 {end_date}。
            使用網路搜尋工具來尋找三個航班選項和三個飯店選項。
          expected_output: >-
            一個包含三個航班選項和三個飯店選項的列表，每個選項都包含詳細的資訊，如價格、航空公司、飯店星級等。

        plan_itinerary:
          description: >-
            根據使用者的興趣 {interests}，為這趟在 {destination} 為期 {duration}
            的旅程規劃一份詳細的每日行程。
            使用網路搜尋工具尋找必訪景點、三家評價高的特色餐廳，和一個特殊的在地體驗。
            對於其中一家你最推薦的餐廳，請使用網站讀取工具訪問其官方網站，並在行程中加入它的特色菜或營業時間等詳細資訊。
          expected_output: >-
            一份詳細的每日旅遊行程，包含景點、餐廳和在地體驗的建議。
            行程應以 Markdown 格式呈現，並確保內容豐富且引人入勝。

        create_travel_guide:
          description: >-
            你的最終任務是將前面步驟提供的所有旅遊資訊，
            合併成一個完整的 Markdown 格式字串。
            然後，你 **必須** 使用 `File Writer Tool` 這個工具將字串寫入檔案。
            這個工具只接受兩個參數：'file_path' 和 'text'。
            請將 `file_path` 的值設定為 '/app/my_travel_planner/旅遊手冊.md'，
            並將你合併好的完整 Markdown 字串作為 `text` 參數的值。
          expected_output: >-
            一個簡單的確認訊息，說明檔案已寫入。例如："已成功將旅遊手冊儲存至 /app/my_travel_planner/旅遊手冊.md"。
        ```

4.  **編排 Crew (`crew.py`)**
    *   **檔案**：`my_travel_planner/src/my_travel_planner/crew.py`
    *   **操作**：用以下內容覆蓋整個檔案，這會將 Agents 和 Tasks 正確地組裝起來。
        ```python
        from crewai import Agent, Crew, Process, Task
        from crewai.project import CrewBase, agent, crew, task
        from crewai_tools import SerperDevTool, ScrapeWebsiteTool, FileWriterTool

        @CrewBase
        class MyTravelPlannerCrew():
            """MyTravelPlanner crew"""
            agents_config = 'config/agents.yaml'
            tasks_config = 'config/tasks.yaml'

            def __init__(self) -> None:
                self.serper_tool = SerperDevTool()
                self.scrape_tool = ScrapeWebsiteTool()
                self.file_writer_tool = FileWriterTool()

            @agent
            def expert_travel_agent(self) -> Agent:
                return Agent(config=self.agents_config['expert_travel_agent'], tools=[self.serper_tool], verbose=True)

            @agent
            def local_expert(self) -> Agent:
                return Agent(config=self.agents_config['local_expert'], tools=[self.serper_tool, self.scrape_tool], verbose=True)

            @agent
            def travel_concierge(self) -> Agent:
                return Agent(config=self.agents_config['travel_concierge'], tools=[self.file_writer_tool], verbose=True)

            @task
            def identify_flights_and_hotels(self) -> Task:
                return Task(config=self.tasks_config['identify_flights_and_hotels'], agent=self.expert_travel_agent())

            @task
            def plan_itinerary(self) -> Task:
                return Task(config=self.tasks_config['plan_itinerary'], agent=self.local_expert(), context=[self.identify_flights_and_hotels()])

            @task
            def create_travel_guide(self) -> Task:
                return Task(config=self.tasks_config['create_travel_guide'], agent=self.travel_concierge(), context=[self.plan_itinerary(), self.identify_flights_and_hotels()])

            @crew
            def crew(self) -> Crew:
                return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=2)
        ```

5.  **設定入口參數 (`main.py`)**
    *   **檔案**：`my_travel_planner/src/my_travel_planner/main.py`
    *   **操作**：修改 `run()` 函式中的 `inputs` 字典，填入我們的旅遊需求。
        ```python
        # ... (imports) ...
        def run():
            """Run the crew."""
            inputs = {
                'destination': '日本東京',
                'duration': '7天',
                'interests': '風景、美食、文化',
                'start_date': '2025-07-07',
                'end_date': '2025-07-13',
            }
            MyTravelPlannerCrew().crew().kickoff(inputs=inputs)
        # ... (other functions) ...
        ```

### 步驟 3: 封裝並執行您的應用

客製化完成後，我們為這個專案建立一個最終的可執行映像檔。

1.  **建立專案 Dockerfile**
    *   在**專案根目錄** (`crewai-projects/`) 下，建立一個名為 `Dockerfile` 的檔案。
    *   **內容如下**：
        ```dockerfile
        # 使用我們預先建置好的工具箱
        FROM crewai-toolkit

        # 將我們客製化的專案複製到容器中
        COPY ./my_travel_planner /app/my_travel_planner

        # 將工作目錄設定到專案內部
        WORKDIR /app/my_travel_planner

        # 安裝專案，這會使其執行指令生效
        RUN pip install -e .

        # 設定預設指令為執行專案
        # 'my_travel_planner' 指令來自 pyproject.toml 中 [project.scripts] 的定義
        CMD ["my_travel_planner"]
        ```

2.  **建置最終應用程式映像檔**
    在終端機中（仍在 `crewai-projects/` 目錄下），執行：
    ```bash
    docker build -t travel-planner-app .
    ```

3.  **執行您的 AI Crew！**
    萬事俱備！執行以下指令來啟動您的 AI 旅遊規劃師：
    ```bash
    docker run --rm --env-file ./my_travel_planner/.env -v "$(pwd)/my_travel_planner:/app/my_travel_planner" travel-planner-app
    ```
    *   `--env-file`: 載入包含 API 金鑰的檔案。
    *   `-v ...`: 將您的專案資料夾掛載進去。這讓您**未來修改 Python 程式碼後無需重新 build**，並且，最終產出的報告會直接出現在 `my_travel_planner` 資料夾中。

程式執行完畢後，您將在 `my_travel_planner` 資料夾中找到 `旅遊手冊.md`。恭喜！