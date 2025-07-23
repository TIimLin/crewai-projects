'use client';

import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import styles from '../styles/App.module.css';

interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface TaskStatus {
  query: string;
  status: 'idle' | 'thinking' | 'analyzing' | 'processing' | 'generating' | 'completed' | 'error';
  current_agent: string;
  progress: number;
  steps: Array<{
    timestamp: string;
    agent: string;
    step: string;
    status: string;
  }>;
  result?: any;
  error?: string;
  started_at: string;
  completed_at?: string;
}

// Agent 狀態枚舉
enum AgentState {
  IDLE = 'idle',
  THINKING = 'thinking',
  ANALYZING = 'analyzing',
  PROCESSING = 'processing',
  GENERATING = 'generating',
  AWAITING_HUMAN_INPUT = 'awaiting_human_input',
  COMPLETED = 'completed',
  ERROR = 'error'
}

// Agent 狀態資訊
interface AgentInfo {
  state: AgentState;
  currentStep: string;
  progress: number;
  details: string[];
  error?: string;
  humanInputPrompt?: string;
}

// Markdown 渲染函數
const renderMarkdownContent = (content: string) => {
  try {
    return (
      <div className={styles.markdownContent}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    );
  } catch (error) {
    console.error('ReactMarkdown渲染錯誤:', error);
    // 備用方案：基本的 HTML 轉換
    const processMarkdown = (text: string) => {
      // 處理標題
      let html = text
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/^### (.*$)/gim, '<h3>$1</h3>')
        .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

      // 更好的列表處理
      const lines = html.split('\n');
      const processedLines: string[] = [];
      let inList = false;
      let listLevel = 0;
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const listMatch = line.match(/^(\s*)\*\s+(.*)/);
        
        if (listMatch) {
          const indentLevel = Math.floor(listMatch[1].length / 4); // 假設每4個空格為一個縮排層級
          
          if (!inList) {
            processedLines.push('<ul style="margin: 0.5rem 0; padding-left: 1.2rem; list-style: none;">');
            inList = true;
            listLevel = indentLevel;
          } else if (indentLevel > listLevel) {
            processedLines.push('<ul style="margin: 0.1rem 0; padding-left: 1rem; list-style: none;">');
            listLevel = indentLevel;
          } else if (indentLevel < listLevel) {
            for (let j = listLevel; j > indentLevel; j--) {
              processedLines.push('</ul>');
            }
            listLevel = indentLevel;
          }
          
          processedLines.push(`<li style="margin: 0.1rem 0; line-height: 1.4; padding-left: 0.1rem; position: relative;"><span style="position: absolute; left: -1em; color: #667eea; font-weight: bold;">•</span>${listMatch[2]}</li>`);
        } else {
          if (inList) {
            for (let j = 0; j <= listLevel; j++) {
              processedLines.push('</ul>');
            }
            inList = false;
            listLevel = 0;
          }
          
          if (line.trim()) {
            processedLines.push(`<p style="margin: 0.4rem 0; line-height: 1.5;">${line}</p>`);
          } else {
            processedLines.push('');
          }
        }
      }
      
      // 如果最後還在列表中，關閉所有列表
      if (inList) {
        for (let j = 0; j <= listLevel; j++) {
          processedLines.push('</ul>');
        }
      }
      
      return processedLines.join('\n');
    };

    return (
      <div className={styles.markdownContent} 
           dangerouslySetInnerHTML={{ 
             __html: processMarkdown(content)
           }} 
      />
    );
  }
};

const LTCChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [humanInputValue, setHumanInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAwaitingHumanInput, setIsAwaitingHumanInput] = useState(false);
  const [agentInfo, setAgentInfo] = useState<AgentInfo>({
    state: AgentState.IDLE,
    currentStep: '待機中',
    progress: 0,
    details: [],
    humanInputPrompt: ''
  });
  const [expandedDetails, setExpandedDetails] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // 自動捲動到最新訊息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 清理 EventSource
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const connectToTaskStream = (taskId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource(`http://localhost:8000/status-stream/${taskId}`);
    eventSourceRef.current = eventSource;

    eventSource.onmessage = (event) => {
      try {
        const status = JSON.parse(event.data);
        
        // 更新 agentInfo 來匹配原本的介面
        setAgentInfo(prev => ({
          ...prev,
          state: status.status as AgentState,
          currentStep: status.current_agent || getStatusText(status.status),
          progress: status.progress,
          details: status.step ? [...prev.details, status.step] : prev.details,
          error: status.error,
          humanInputPrompt: status.status === AgentState.AWAITING_HUMAN_INPUT 
            ? `AI 正在等待您的回饋：\n"${status.step}"` 
            : prev.humanInputPrompt
        }));
        
        if (status.status === AgentState.AWAITING_HUMAN_INPUT) {
          setIsLoading(true); // 保持加載狀態
          setIsAwaitingHumanInput(true);
        } else {
          setIsAwaitingHumanInput(false);
        }

        // 當任務完成時停止載入狀態
        if (status.status === 'completed') {
          setIsLoading(false);
          if (status.result?.raw) {
            const botMessage: Message = {
              id: (Date.now() + 1).toString(),
              content: status.result.raw,
              isUser: false,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, botMessage]);
          }
          eventSource.close();
        } else if (status.status === 'error') {
          setIsLoading(false);
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: `抱歉，處理您的請求時發生錯誤：${status.error}`,
            isUser: false,
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
          eventSource.close();
        }
      } catch (error) {
        console.error('解析 SSE 資料時發生錯誤:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE 連接錯誤:', error);
      eventSource.close();
    };
  };

  const getStatusText = (status: string) => {
    const statusMap = {
      idle: '待機中',
      thinking: '思考中',
      analyzing: '分析中',
      processing: '處理中',
      generating: '生成報告',
      awaiting_human_input: '等待使用者輸入',
      completed: '完成諮詢',
      error: '處理錯誤'
    };
    return statusMap[status as keyof typeof statusMap] || status;
  };

  // 處理範例問題點擊
  const handleExampleClick = (exampleText: string) => {
    if (isLoading) return; // 防止在載入中時點擊
    
    // 直接發送範例問題
    const userMessage: Message = {
      id: Date.now().toString(),
      content: exampleText,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue(''); // 清空輸入框
    setIsLoading(true);

    // 重置 Agent 狀態
    setAgentInfo({
      state: AgentState.THINKING,
      currentStep: '開始分析',
      progress: 0,
      details: [],
      humanInputPrompt: ''
    });

    // 發送請求到後端
    fetch('http://localhost:8000/invoke', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_query: exampleText })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success && data.task_id) {
        setCurrentTaskId(data.task_id);
        connectToTaskStream(data.task_id);
      } else {
        setIsLoading(false);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: '抱歉，無法啟動諮詢服務，請稍後再試。',
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: '抱歉，系統發生錯誤，請稍後再試。',
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
      
      setAgentInfo(prev => ({
        ...prev,
        state: AgentState.ERROR,
        currentStep: '處理失敗',
        error: '系統錯誤'
      }));
      setIsLoading(false);
    });
  };

  const handleHumanSubmit = async () => {
    if (!humanInputValue.trim() || !currentTaskId) return;

    setIsLoading(true);
    setIsAwaitingHumanInput(false);

    try {
      const response = await fetch(`http://localhost:8000/continue/${currentTaskId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input: humanInputValue }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit human input');
      }

      setHumanInputValue('');
      setAgentInfo(prev => ({
        ...prev,
        state: AgentState.PROCESSING,
        currentStep: '已收到您的回饋，繼續處理...',
        humanInputPrompt: '',
      }));

    } catch (error) {
      console.error('Error submitting human input:', error);
      // Handle error display
      setAgentInfo(prev => ({
        ...prev,
        state: AgentState.ERROR,
        currentStep: '提交回饋失敗',
        error: '無法提交您的回饋，請檢查後端連線。',
      }));
    }
  };


  // 發送訊息到後端
  const sendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      isUser: true,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // 重置 Agent 狀態
    setAgentInfo({
      state: AgentState.THINKING,
      currentStep: '開始分析',
      progress: 0,
      details: [],
      humanInputPrompt: ''
    });

    try {
      // 實際 API 呼叫
      const response = await fetch('http://localhost:8000/invoke', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_query: inputValue })
      });

      const data = await response.json();
      
      if (data.success && data.task_id) {
        setCurrentTaskId(data.task_id);
        connectToTaskStream(data.task_id);
      } else {
        setIsLoading(false);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: '抱歉，無法啟動諮詢服務，請稍後再試。',
          isUser: false,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      }

    } catch (error) {
      console.error('Error:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: '抱歉，系統發生錯誤，請稍後再試。',
        isUser: false,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
      
      setAgentInfo(prev => ({
        ...prev,
        state: AgentState.ERROR,
        currentStep: '處理失敗',
        error: '系統錯誤'
      }));
      setIsLoading(false);
    }
  };

  // 獲取狀態圖示
  const getStateIcon = (state: AgentState) => {
    switch (state) {
      case AgentState.THINKING: return '🤔';
      case AgentState.ANALYZING: return '🔍';
      case AgentState.PROCESSING: return '⚙️';
      case AgentState.GENERATING: return '📝';
      case AgentState.AWAITING_HUMAN_INPUT: return '👤';
      case AgentState.COMPLETED: return '✅';
      case AgentState.ERROR: return '❌';
      default: return '💤';
    }
  };

  // 獲取狀態顏色
  const getStateColor = (state: AgentState) => {
    switch (state) {
      case AgentState.THINKING: return '#3b82f6';
      case AgentState.ANALYZING: return '#f59e0b';
      case AgentState.PROCESSING: return '#8b5cf6';
      case AgentState.GENERATING: return '#10b981';
      case AgentState.AWAITING_HUMAN_INPUT: return '#f97316';
      case AgentState.COMPLETED: return '#059669';
      case AgentState.ERROR: return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className={styles.app}>
      <div className={styles.appHeader}>
        <h1>🏥 台灣長照諮詢系統</h1>
        <p>專業的長期照護諮詢服務，為您提供個人化的照護建議</p>
      </div>
      
      <div className={styles.appContent}>
        {/* 聊天區域 */}
        <div className={styles.chatSection}>
          <div className={styles.messagesContainer}>
            {messages.length === 0 ? (
              <div className={styles.welcomeMessage}>
                <h3>歡迎使用長照諮詢系統！</h3>
                <p>請描述您的照護需求，我們將為您提供專業的建議和資源推薦。</p>
                <div className={styles.exampleQueries}>
                  <p>範例問題：</p>
                  <ul>
                    <li onClick={() => handleExampleClick("我需要為80歲的母親尋找居家照護服務")}>
                      我需要為80歲的母親尋找居家照護服務
                    </li>
                    <li onClick={() => handleExampleClick("請推薦台北市的日間照顧中心")}>
                      請推薦台北市的日間照顧中心
                    </li>
                    <li onClick={() => handleExampleClick("長照2.0的申請流程是什麼？")}>
                      長照2.0的申請流程是什麼？
                    </li>
                  </ul>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`${styles.message} ${message.isUser ? styles.userMessage : styles.botMessage}`}
                >
                  <div className={styles.messageContent}>
                    <div className={styles.messageText}>
                      {message.isUser ? (
                        message.content
                      ) : (
                        renderMarkdownContent(message.content)
                      )}
                    </div>
                    <div className={styles.messageTime}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))
            )}
            {isAwaitingHumanInput && (
              <div className={styles.humanInputSection}>
                <h4>{agentInfo.humanInputPrompt || 'AI 正在等待您的回饋...'}</h4>
                <p>請在此輸入您的補充說明或修改建議，然後點擊提交。</p>
                <div className={styles.inputContainer}>
                  <textarea
                    value={humanInputValue}
                    onChange={(e) => setHumanInputValue(e.target.value)}
                    placeholder="請輸入您的回饋..."
                    className={styles.humanInputTextarea}
                    rows={3}
                  />
                  <button
                    onClick={handleHumanSubmit}
                    disabled={!humanInputValue.trim()}
                    className={styles.sendButton}
                  >
                    提交回饋
                  </button>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 輸入區域 */}
          <div className={styles.inputSection}>
            <div className={styles.inputContainer}>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="請輸入您的長照諮詢需求..."
                disabled={isLoading}
                className={styles.messageInput}
              />
              <button 
                onClick={sendMessage}
                disabled={isLoading || !inputValue.trim()}
                className={styles.sendButton}
              >
                {isLoading ? '處理中...' : '發送'}
              </button>
            </div>
          </div>
        </div>
        
        {/* Agent 狀態資訊面板 */}
        <div className={styles.infoPanel}>
          <div className={styles.agentStatus}>
            <div className={styles.statusHeader}>
              <h3>🤖 AI 助理狀態</h3>
            </div>
            
            <div className={styles.statusCard}>
              <div className={styles.statusMain}>
                <div className={styles.statusIcon} style={{ color: getStateColor(agentInfo.state) }}>
                  {getStateIcon(agentInfo.state)}
                </div>
                <div className={styles.statusInfo}>
                  <div className={styles.statusText}>{agentInfo.currentStep}</div>
                  <div className={styles.statusState}>{agentInfo.state}</div>
                </div>
              </div>
              
              {agentInfo.progress > 0 && (
                <div className={styles.progressContainer}>
                  <div className={styles.progressBar}>
                    <div 
                      className={styles.progressFill} 
                      style={{ 
                        width: `${agentInfo.progress}%`,
                        backgroundColor: getStateColor(agentInfo.state)
                      }}
                    />
                  </div>
                  <div className={styles.progressText}>{agentInfo.progress}%</div>
                </div>
              )}
            </div>
            
            {agentInfo.details.length > 0 && (
              <div className={styles.executionDetails}>
                <button 
                  className={styles.detailsToggle}
                  onClick={() => setExpandedDetails(!expandedDetails)}
                >
                  執行詳情 {expandedDetails ? '▼' : '▶'}
                </button>
                {expandedDetails && (
                  <div className={styles.detailsList}>
                    {agentInfo.details.map((detail, index) => (
                      <div key={index} className={styles.detailItem}>
                        <span className={styles.detailMarker}>•</span>
                        <span className={styles.detailText}>{detail}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {agentInfo.error && (
              <div className={styles.errorMessage}>
                <span className={styles.errorIcon}>⚠️</span>
                {agentInfo.error}
              </div>
            )}
          </div>
          
          <div className={styles.systemInfo}>
            <h4>系統資訊</h4>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>模型:</span>
              <span className={styles.infoValue}>Gemini 2.5 Flash</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>狀態:</span>
              <span className={styles.infoValue}>線上</span>
            </div>
            <div className={styles.infoItem}>
              <span className={styles.infoLabel}>版本:</span>
              <span className={styles.infoValue}>1.0.0</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LTCChat; 