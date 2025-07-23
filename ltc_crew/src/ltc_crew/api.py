from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ltc_crew.crew import LtcCrew
import os
import json
import asyncio
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List
import uuid

app = FastAPI(title="台灣長照諮詢系統 API", version="1.0.0")

# 添加 CORS 中介軟體
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 開發服務器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    GENERATING = "generating"
    AWAITING_HUMAN_INPUT = "awaiting_human_input"
    COMPLETED = "completed"
    ERROR = "error"

class UserQuery(BaseModel):
    user_query: str

class HumanInput(BaseModel):
    input: str

# 全域狀態管理
class TaskManager:
    """管理 CrewAI 任務的狀態和進度"""
    def __init__(self):
        self._lock = asyncio.Lock()
        self.tasks = {}
        self.crews = {}

    async def create_task(self, query: str) -> str:
        """建立一個新任務並返回任務 ID"""
        async with self._lock:
            task_id = str(uuid.uuid4())
            self.tasks[task_id] = {
                "id": task_id,
                "query": query,
                "status": AgentState.IDLE,
                "current_agent": "",
                "progress": 0,
                "step": "Task created",
                "result": None,
                "error": None,
                "human_input_event": asyncio.Event()
            }
            # 為這個任務創建一個新的 crew 實例
            ltc_crew_instance = LtcCrew()
            self.crews[task_id] = ltc_crew_instance.crew()
            return task_id

    async def update_status(self, task_id: str, status: AgentState, agent: str = "", progress: int = 0, step: str = ""):
        """更新任務狀態"""
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task['status'] = status
                if agent:
                    task['current_agent'] = agent
                if progress > 0:
                    task['progress'] = progress
                if step:
                    task['step'] = step

    async def set_human_input(self, task_id: str, data: str):
        """設定人類輸入並觸發事件"""
        async with self._lock:
            if task_id in self.tasks and self.tasks[task_id]["status"] == AgentState.AWAITING_HUMAN_INPUT:
                self.tasks[task_id]["human_input_data"] = data
                self.tasks[task_id]["human_input_event"].set()
                return True
        return False

    async def wait_for_human_input(self, task_id: str):
        # This function is now deprecated and will be removed.
        # The logic is handled by await_human_input.
        pass

    async def await_human_input(self, task_id: str, message: str):
        """將任務狀態更新為等待人類輸入"""
        await self.update_status(
            task_id, 
            AgentState.AWAITING_HUMAN_INPUT, 
            step=message
        )

    async def complete_task(self, task_id: str, result: Any):
        """將任務標記為完成"""
        async with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = AgentState.COMPLETED
                self.tasks[task_id]["progress"] = 100
                self.tasks[task_id]["result"] = result
                self.tasks[task_id]["completed_at"] = datetime.now().isoformat()

    async def error_task(self, task_id: str, error: str):
        async with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = AgentState.ERROR
                self.tasks[task_id]["error"] = error

    async def get_task(self, task_id: str):
        async with self._lock:
            return self.tasks.get(task_id)

    async def get_crew(self, task_id: str):
        """獲取與任務相關的 crew 實例"""
        async with self._lock:
            return self.crews.get(task_id)

task_manager = TaskManager()

async def run_crew_task(task_id: str, query: str):
    """在背景執行 CrewAI 任務並處理人類輸入"""
    try:
        await task_manager.update_status(task_id, AgentState.PROCESSING, progress=10, step="Initializing crew...")
        
        crew = await task_manager.get_crew(task_id)
        if not crew:
            await task_manager.error_task(task_id, "Crew not found for this task.")
            return

        inputs = {'user_query': query}
        
        await task_manager.update_status(task_id, AgentState.PROCESSING, progress=20, step="Starting crew kickoff...")
        
        # 使用 asyncio.to_thread 在背景執行緒中運行同步的 kickoff
        result = await asyncio.to_thread(crew.kickoff, inputs=inputs)
        
        # 由於 crewAI 會自動處理 human_input 流程，這裡不再需要手動檢查
        # await task_manager.await_human_input(task_id, "The crew is waiting for your input.")

        await task_manager.update_status(task_id, AgentState.GENERATING, progress=90, step="Generating final report...")

        if not os.path.exists('reports'):
            os.makedirs('reports')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"reports/report_{timestamp}.md"
        
        final_output = result.raw if hasattr(result, 'raw') else str(result)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(final_output)
            
        final_result = result.model_dump() if hasattr(result, 'model_dump') else {"raw": final_output}
        final_result['report_path'] = file_path
        
        await task_manager.complete_task(task_id, final_result)
        
    except Exception as e:
        print(f"Error during crew execution for task {task_id}: {e}")
        await task_manager.error_task(task_id, str(e))

@app.post("/invoke")
async def invoke_crew(query: UserQuery):
    """啟動 CrewAI 任務並返回任務 ID"""
    task_id = await task_manager.create_task(query.user_query)
    
    # 在背景異步執行任務
    asyncio.create_task(run_crew_task(task_id, query.user_query))
    
    return {
        "success": True,
        "task_id": task_id,
        "message": "任務已啟動，請使用 /status 端點追蹤進度"
    }

async def continue_crew(task_id: str, human_input: HumanInput):
    """接收人類輸入並繼續任務"""
    crew = await task_manager.get_crew(task_id)
    if not crew:
        raise HTTPException(status_code=404, detail="Task not found or no active crew.")

    # crewAI 會自動處理輸入，我們只需要將輸入傳遞下去
    # 然後再次 kickoff 來繼續執行
    def resume_crew():
        return crew.kickoff(inputs={"human_input": human_input.input})

    # 在背景執行緒中繼續執行
    result = await asyncio.to_thread(resume_crew)

    # 任務完成後，human_input 狀態會自動解除，這裡也不再需要檢查
    # if crew.human_input:
    # ...

    # 任務完成
    await task_manager.update_status(task_id, AgentState.GENERATING, progress=90, step="Generating final report...")

    if not os.path.exists('reports'):
        os.makedirs('reports')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"reports/report_{timestamp}.md"
    
    final_output = result.raw if hasattr(result, 'raw') else str(result)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final_output)
        
    final_result = result.model_dump() if hasattr(result, 'model_dump') else {"raw": final_output}
    final_result['report_path'] = file_path
    
    await task_manager.complete_task(task_id, final_result)

    return {"success": True, "message": "Input received, task completed."}


@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """獲取任務狀態"""
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任務不存在")
    
    # We need to create a copy and remove non-serializable objects
    task_copy = task.copy()
    task_copy.pop("human_input_event", None)
    
    return task_copy

@app.get("/status-stream/{task_id}")
async def status_stream(task_id: str):
    """Server-Sent Events 即時狀態更新"""
    async def generate():
        last_status = None
        while True:
            task = await task_manager.get_task(task_id)
            if not task:
                break
            
            # Create a serializable copy of the task status
            task_copy = task.copy()
            task_copy.pop("human_input_event", None)
            
            current_agent = task_copy.get("current_agent", "")
            current_status = (task_copy["status"], task_copy["progress"], current_agent)

            if current_status != last_status:
                status_data = {
                    "status": task_copy["status"],
                    "progress": task_copy["progress"],
                    "current_agent": current_agent,
                    "step": task_copy.get("step", ""),
                    "result": task_copy.get("result"),
                    "error": task_copy.get("error")
                }
                yield f"data: {json.dumps(status_data)}\n\n"
                last_status = current_status

            if task["status"] in [AgentState.COMPLETED, AgentState.ERROR]:
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/")
async def root():
    return {
        "message": "台灣長照諮詢系統 API 正在運行",
        "version": "1.0.0",
        "model": "Gemini 2.5 Flash",
        "status": "online"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()} 