// src/Chat.jsx
import { useState, useRef, useEffect } from "react";
// ... (react-icons, react-markdown 등 import) ...
import { FiPaperclip, FiPlusSquare, FiCopy } from "react-icons/fi";
import { FaRecycle } from 'react-icons/fa'; 
import ReactMarkdown from 'react-markdown';


// ⭐️ (제거) const YOUR_PC_IP_ADDRESS = ...
// ⭐️ (제거) const API_BASE_URL = ...

const loadChatHistory = () => {
  // ... (localStorage 로직 동일) ...
  const savedHistory = localStorage.getItem("chat_history");
  if (savedHistory) {
    return JSON.parse(savedHistory);
  } else {
    return [{ role: "assistant", content: "안녕하세요! 무엇이든 물어보세요." }];
  }
};
const defaultMessage = [{ role: "assistant", content: "안녕하세요! 새 대화를 시작합니다." }];

function Chat() {
  // ... (모든 state 선언은 동일) ...
  const [messages, setMessages] = useState(loadChatHistory()); 
  const [input, setInput] = useState("");
  // ... (이하 state) ...

  useEffect(() => {
    // ... (localStorage 저장 로직 동일) ...
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
    if (messages.length > 0) {
      localStorage.setItem("chat_history", JSON.stringify(messages));
    } else {
      localStorage.removeItem("chat_history");
    }
  }, [messages]); 

  // ... (handleFileChange 로직 동일) ...
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
    e.target.value = null; 
  };
  
  // ... (handleChatSubmitWithText 로직 수정) ...
  const handleChatSubmitWithText = async (userMessage, imageContext = null) => {
    // ... (로직 동일) ...
    setIsLoadingChat(true); 
    const contextToUse = imageContext || messages
      .slice()
      .reverse()
      .find(msg => msg.type === "imageAnalysis" && msg.resultData && !msg.resultData.error)
      ?.resultData.main_class || null;

    const chatPayload = {
      message: userMessage,
      image_context: contextToUse,
    };
    setMessages((prev) => [
      ...prev, 
      { role: "user", content: userMessage },
      { role: "assistant", content: "" } 
    ]);
    
    try {
      // ⭐️ (수정) IP 주소 제거 -> 상대 경로 (Vite 프록시가 처리)
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(chatPayload),
      });
      // ... (이하 스트리밍 로직 동일) ...
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Server error: ${res.status} - ${errorText}`);
      }
      const reader = res.body.getReader();
      // ... (while(true) ... reader.read() ...) ...
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
      // ... (오류 처리 동일) ...
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

  // ... (handleSubmitFromForm 로직 수정) ...
  const handleSubmitFromForm = async (e) => {
    // ... (로직 동일) ...
    e.preventDefault(); 
    const userMessage = input.trim();
    const imageFile = file;
    const tempPreviewUrl = preview;
    if (!userMessage && !imageFile) return; 
    setInput("");
    setFile(null);
    setPreview(null); 
    let imageContext = null;

    if (imageFile) {
      // ... (이미지 처리 로직 동일) ...
      setIsLoadingImage(true); 
      const formData = new FormData();
      formData.append("file", imageFile);
      try {
        // ⭐️ (수정) IP 주소 제거 -> 상대 경로 (Vite 프록시가 처리)
        const res = await fetch("/api/predict", {
          method: "POST",
          body: formData,
        });
        // ... (이하 이미지 처리 동일) ...
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
        // ... (오류 처리 동일) ...
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

    if (userMessage) {
      await handleChatSubmitWithText(userMessage, imageContext);
    }
  };

  // ... (handleExamplePrompt, canSubmit, handleNewChat, handleCopy, getButtonText 동일) ...
  const handleExamplePrompt = (promptText) => {
    setInput(promptText);
    handleChatSubmitWithText(promptText);
  };
  const canSubmit = !isLoadingChat && !isLoadingImage && (!!input.trim() || !!file);
  const handleNewChat = () => {
    setMessages(defaultMessage);
    localStorage.removeItem("chat_history");
  };
  const handleCopy = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert("답변이 복사되었습니다.");
    }).catch(err => {
      console.error("복사 실패:", err);
    });
  };
  const getButtonText = () => {
    if (isLoadingImage) return "분석 중...";
    if (isLoadingChat) return "답변 중...";
    return "전송";
  };

  // ... (return JSX 부분은 동일, 수정 없음) ...
  return (
    <div className="chat-container">
      {/* ... (헤더) ... */}
      <div className="chat-header">...</div>
      {/* ... (메시지 리스트) ... */}
      <div className="message-list" ref={messageListRef}>...</div>
      {/* ... (입력 폼) ... */}
      <form className="chat-input-form" onSubmit={handleSubmitFromForm}>
        {/* ... (미리보기) ... */}
        {preview && (
          <div className="staged-image-preview">...</div>
        )}
        {/* ... (입력 행) ... */}
        <div className="input-row">
          <label htmlFor="image-upload" className="image-upload-button">
            <FiPaperclip />
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