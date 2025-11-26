import { useState, useRef, useEffect } from "react";
import { FiPaperclip, FiPlusSquare, FiCopy } from "react-icons/fi";
import { FaRecycle } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';

// 로컬 스토리지에서 채팅 기록 불러오기
const loadChatHistory = () => {
  const savedHistory = localStorage.getItem("chat_history");
  if (savedHistory) {
    return JSON.parse(savedHistory);
  } else {
    return [{ role: "assistant", content: "안녕하세요! 무엇이든 물어보세요." }];
  }
};

const defaultMessage = [{ role: "assistant", content: "안녕하세요! 새 대화를 시작합니다." }];

function Chat() {
  // ---------------------------------------------------------
  // ⭐️ [수정됨] 누락되었던 상태(State) 변수들을 모두 선언했습니다.
  // ---------------------------------------------------------
  const [messages, setMessages] = useState(loadChatHistory());
  const [input, setInput] = useState("");
  
  // 에러 원인이었던 변수들 추가
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [isLoadingImage, setIsLoadingImage] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const messageListRef = useRef(null);
  // ---------------------------------------------------------

  // 채팅 기록이 변경될 때마다 스크롤 이동 및 저장
  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
    if (messages.length > 0) {
      localStorage.setItem("chat_history", JSON.stringify(messages));
    } else {
      localStorage.removeItem("chat_history");
    }
  }, [messages]);

  // 파일 선택 핸들러
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
    e.target.value = null;
  };

  // 텍스트 채팅 전송 (스트리밍)
  const handleChatSubmitWithText = async (userMessage, imageContext = null) => {
    setIsLoadingChat(true);

    // 이미지 분석 결과가 있다면 컨텍스트로 사용
    const contextToUse = imageContext || messages
      .slice()
      .reverse()
      .find(msg => msg.type === "imageAnalysis" && msg.resultData && !msg.resultData.error)
      ?.resultData.main_class || null;

    const chatPayload = {
      message: userMessage,
      image_context: contextToUse,
    };

    // 사용자 메시지 즉시 추가
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
      { role: "assistant", content: "" }
    ]);

    try {
      // ⭐️ 상대 경로 사용 (Vite 프록시가 백엔드로 전달)
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(chatPayload),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Server error: ${res.status} - ${errorText}`);
      }

      // 스트리밍 응답 처리
      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let firstChunk = true;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        if (firstChunk) {
          setIsLoadingChat(false);
          firstChunk = false;
        }

        setMessages((prevMessages) => {
          const lastMessage = prevMessages[prevMessages.length - 1];
          const updatedMessage = {
            ...lastMessage,
            content: lastMessage.content + chunk,
          };
          return [...prevMessages.slice(0, -1), updatedMessage];
        });
      }
    } catch (error) {
      console.error("Chat Error:", error);
      setIsLoadingChat(false);
      setMessages((prevMessages) => {
        const lastMessage = prevMessages[prevMessages.length - 1];
        const updatedMessage = {
          ...lastMessage,
          content: `채팅 오류: ${error.message}`,
        };
        return [...prevMessages.slice(0, -1), updatedMessage];
      });
    }

    if (isLoadingChat) setIsLoadingChat(false);
  };

  // 폼 전송 핸들러 (이미지 + 텍스트)
  const handleSubmitFromForm = async (e) => {
    e.preventDefault();
    const userMessage = input.trim();
    const imageFile = file;
    const tempPreviewUrl = preview;

    if (!userMessage && !imageFile) return;

    setInput("");
    setFile(null);
    setPreview(null);
    let imageContext = null;

    // 1. 이미지가 있다면 먼저 분석 요청
    if (imageFile) {
      setIsLoadingImage(true);
      const formData = new FormData();
      formData.append("file", imageFile);

      try {
        // ⭐️ 상대 경로 사용 (Vite 프록시)
        const res = await fetch("/api/predict", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        
        const data = await res.json();
        
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            type: "imageAnalysis",
            previewUrl: tempPreviewUrl,
            resultData: data
          }
        ]);

        if (!data.error) {
          imageContext = data.main_class;
        }
      } catch (error) {
        console.error("Fetch Error (Image Analysis):", error);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            type: "imageAnalysis",
            previewUrl: tempPreviewUrl,
            resultData: { error: `이미지 분석에 실패했습니다. (${error.message})` }
          }
        ]);
      }
      setIsLoadingImage(false);
    }

    // 2. 텍스트 메시지가 있다면 채팅 요청
    if (userMessage) {
      await handleChatSubmitWithText(userMessage, imageContext);
    }
  };

  const handleExamplePrompt = (promptText) => {
    setInput(promptText);
    handleChatSubmitWithText(promptText);
  };

  const handleNewChat = () => {
    if (window.confirm("대화 내용을 초기화하시겠습니까?")) {
        setMessages(defaultMessage);
        localStorage.removeItem("chat_history");
    }
  };

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert("내용이 복사되었습니다.");
    }).catch(err => {
      console.error("복사 실패:", err);
    });
  };

  const getButtonText = () => {
    if (isLoadingImage) return "분석 중...";
    if (isLoadingChat) return "답변 중...";
    return "전송";
  };

  const canSubmit = !isLoadingChat && !isLoadingImage && (!!input.trim() || !!file);

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FaRecycle size={24} color="#2ecc71" />
            <h2>재활용 챗봇</h2>
        </div>
        <button onClick={handleNewChat} className="new-chat-btn" title="새 대화 시작">
            <FiPlusSquare size={20} />
        </button>
      </div>

      <div className="message-list" ref={messageListRef}>
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-row ${msg.role}`}>
            {msg.role === "assistant" && (
                <div className="avatar assistant-avatar">AI</div>
            )}
            
            <div className={`message-bubble ${msg.role}-bubble`}>
                {/* 이미지 분석 결과 표시 */}
                {msg.type === "imageAnalysis" && (
                    <div className="analysis-result">
                        {msg.previewUrl && (
                            <img src={msg.previewUrl} alt="Upload Preview" className="uploaded-image" />
                        )}
                        {msg.resultData?.error ? (
                            <div className="error-msg">⚠️ {msg.resultData.error}</div>
                        ) : (
                           msg.resultData && (
                            <div className="detection-info">
                                <p><strong>감지된 물체:</strong> {msg.resultData.main_class}</p>
                                <p><strong>확률:</strong> {msg.resultData.confidence}%</p>
                                {msg.resultData.recycling_info && (
                                    <div className="recycling-tip">
                                        Tip: {msg.resultData.recycling_info}
                                    </div>
                                )}
                            </div>
                           )
                        )}
                    </div>
                )}

                {/* 텍스트 메시지 표시 (마크다운) */}
                {msg.content && (
                    <div className="markdown-content">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                )}
                
                {/* 복사 버튼 (Assistant 메시지에만) */}
                {msg.role === "assistant" && msg.content && (
                    <button className="copy-btn" onClick={() => handleCopy(msg.content)}>
                        <FiCopy />
                    </button>
                )}
            </div>
          </div>
        ))}
        {isLoadingChat && <div className="message-row assistant"><div className="loading-dots">...</div></div>}
      </div>

      <form className="chat-input-form" onSubmit={handleSubmitFromForm}>
        {preview && (
          <div className="staged-image-preview">
            <img src={preview} alt="Preview" />
            <button type="button" onClick={() => { setFile(null); setPreview(null); }}>×</button>
          </div>
        )}
        
        <div className="input-row">
          <label htmlFor="image-upload" className="image-upload-button">
            <FiPaperclip size={20} />
          </label>
          <input
            id="image-upload"
            type="file"
            accept="image/*, .jpg, .jpeg, .png, .gif, .webp, .heic, .heif"
            onChange={handleFileChange}
            disabled={isLoadingChat || isLoadingImage}
            style={{ display: "none" }}
          />
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="메시지를 입력하세요..."
            disabled={isLoadingChat || isLoadingImage}
          />
          <button type="submit" disabled={!canSubmit}>
            {getButtonText()}
          </button>
        </div>
      </form>
    </div>
  );
}

export default Chat;
