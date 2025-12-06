// src/Chat.jsx (전체 코드 중 handleSubmitWithImageAndText 함수 부분을 집중적으로 수정했습니다)

import { useState, useRef, useEffect } from "react";
import { FiPaperclip, FiCopy } from "react-icons/fi";
import { FaRecycle } from "react-icons/fa";
import ReactMarkdown from "react-markdown";

function Chat({
  storageKey = "chat_history",
  onNewChat,
  onUpdateTitle,
}) {
  // ... (이전 상태값 선언 부분은 동일하므로 유지) ...
  const [messages, setMessages] = useState(() => {
    try {
      const saved = storageKey && localStorage.getItem(storageKey);
      if (saved) return JSON.parse(saved);
      return [];
    } catch (e) {
      console.error("chat history load error:", e);
      return [];
    }
  });

  const [input, setInput] = useState("");
  const [isLoadingChat, setIsLoadingChat] = useState(false);
  const [isLoadingImage, setIsLoadingImage] = useState(false);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const messageListRef = useRef(null);

  // ... (useEffect 및 기타 헬퍼 함수들은 동일하므로 유지) ...

  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
    try {
      if (!storageKey) return;
      if (messages.length > 0) {
        localStorage.setItem(storageKey, JSON.stringify(messages));
      } else {
        localStorage.removeItem(storageKey);
      }
    } catch (e) {
      console.error("chat history save error:", e);
    }
  }, [messages, storageKey]);

  const isEmptyConversation = messages.length === 0;

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
    }
    e.target.value = null;
  };

  const maybeUpdateTitleFromText = (text) => {
    if (!onUpdateTitle) return;
    if (messages.length > 0) return;

    const trimmed = text.trim();
    if (!trimmed) return;
    const maxLen = 20;
    const title =
      trimmed.length > maxLen ? `${trimmed.slice(0, maxLen)}...` : trimmed;
    onUpdateTitle(title);
  };

  // -------------------------------------------------------------
  // 1. 텍스트 채팅 전송 함수 (변경 없음)
  // -------------------------------------------------------------
  const handleChatSubmitWithText = async (userMessage, imageContext = null) => {
    setIsLoadingChat(true);

    // 이미지 컨텍스트가 명시적으로 없으면, 이전 대화 기록에서 가장 최근의 분석 결과를 찾아서 사용
    const contextToUse =
      imageContext ||
      messages
        .slice()
        .reverse()
        .find(
          (msg) =>
            msg.type === "imageAnalysis" &&
            msg.resultData &&
            !msg.resultData.error
        )?.resultData.main_class ||
      null;

    const chatPayload = {
      message: userMessage,
      image_context: contextToUse,
    };

    maybeUpdateTitleFromText(userMessage);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMessage },
      { role: "assistant", content: "" },
    ]);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(chatPayload),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Server error: ${res.status} - ${errorText}`);
      }

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

  const handleWelcomeSubmit = async (e) => {
    e.preventDefault();
    const userMessage = input.trim();
    if (!userMessage && !file) return;

    if (file) {
      await handleSubmitWithImageAndText(userMessage);
    } else {
      setInput("");
      await handleChatSubmitWithText(userMessage, null);
    }
  };

  const handleSubmitFromForm = async (e) => {
    e.preventDefault();
    const userMessage = input.trim();
    if (!userMessage && !file) return;

    await handleSubmitWithImageAndText(userMessage);
  };

  // -------------------------------------------------------------
  // 2. ⭐️ [핵심 수정] 이미지+텍스트 처리 함수 ⭐️
  // -------------------------------------------------------------
  const handleSubmitWithImageAndText = async (userMessage) => {
    const imageFile = file;
    const tempPreviewUrl = preview;

    // 입력창 초기화
    setInput("");
    setFile(null);
    setPreview(null);
    
    let imageContext = null;

    // A. 이미지가 있는 경우 -> 분석 먼저 실행
    if (imageFile) {
      // 미리보기 메시지 추가
      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          type: "imagePreview",
          previewUrl: tempPreviewUrl,
        },
      ]);

      setIsLoadingImage(true);
      const formData = new FormData();
      formData.append("file", imageFile);

      try {
        const res = await fetch("/api/predict", {
          method: "POST",
          body: formData,
        });

        if (!res.ok) throw new Error(`Server error: ${res.status}`);

        const data = await res.json();

        // 분석 결과(확률 등) 메시지 추가
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            type: "imageAnalysis",
            resultData: data,
          },
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
            resultData: {
              error: `이미지 분석에 실패했습니다. (${error.message})`,
            },
          },
        ]);
      }
      setIsLoadingImage(false);
    }

    // B. ⭐️ [수정된 부분] 채팅 설명 요청하기
    // 사용자가 텍스트를 입력했으면 그걸 질문으로 사용하고,
    // 텍스트 없이 이미지만 올렸으면 "자동 질문"을 생성해서 넘깁니다.
    
    let finalQuestion = userMessage;

    // 텍스트가 없고 && 이미지 분석에 성공해서 컨텍스트가 있다면 -> 자동 질문 생성
    if (!finalQuestion && imageContext) {
      finalQuestion = "이 물건의 올바른 분리배출 방법을 알려줘.";
    }

    // 최종적으로 질문할 내용이 있으면 채팅 함수 호출
    if (finalQuestion) {
      await handleChatSubmitWithText(finalQuestion, imageContext);
    }
  };

  const handleExamplePrompt = (promptText) => {
    setInput("");
    handleChatSubmitWithText(promptText);
  };

  const handleCopy = (text) => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        alert("내용이 복사되었습니다.");
      })
      .catch((err) => {
        console.error("복사 실패:", err);
      });
  };

  const getButtonText = () => {
    if (isLoadingImage) return "분석 중...";
    if (isLoadingChat) return "답변 중...";
    return "전송";
  };

  const canSubmit =
    !isLoadingChat && !isLoadingImage && (!!input.trim() || !!file);

  // ... (return 아래 JSX 부분은 디자인이므로 원본 그대로 두시면 됩니다) ...
  return (
    <div className="chat-container">
      {/* ... (기존 JSX 코드 유지) ... */}
      <div className="chat-header">
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <FaRecycle size={24} color="#2ecc71" />
          <h2>EcoBot</h2>
        </div>
      </div>

      {isEmptyConversation ? (
        <div className="welcome-screen">
          <h3>환영합니다! 무엇을 도와드릴까요?</h3>
          <p>
            궁금한 분리수거 방법을 자연어로 물어보거나,
            <br />
            이미지도 업로드해서 도움을 받을 수 있어요.
          </p>

          <div className="example-prompts">
            <button
              onClick={() => handleExamplePrompt("플라스틱 컵은 어떻게 버려?")}
            >
              플라스틱 컵은 어떻게 버려?
            </button>
            <button
              onClick={() =>
                handleExamplePrompt("택배 상자 분리수거 방법 알려줘")
              }
            >
              택배 상자 분리수거
            </button>
            <button
              onClick={() =>
                handleExamplePrompt("우유팩이 일반 종이랑 뭐가 달라?")
              }
            >
              우유팩 분리수거
            </button>
          </div>

          <form className="welcome-input-row" onSubmit={handleWelcomeSubmit}>
            <label
              htmlFor="welcome-image-upload"
              className="image-upload-button"
            >
              <FiPaperclip size={20} />
            </label>
            <input
              id="welcome-image-upload"
              type="file"
              accept="image/*, .jpg, .jpeg, .png, .gif, .webp, .heic, .heif"
              onChange={handleFileChange}
              disabled={isLoadingChat || isLoadingImage}
              style={{ display: "none" }}
            />
            <input
              className="welcome-input"
              type="text"
              placeholder="여기에 질문을 입력해 보세요..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoadingChat || isLoadingImage}
            />
            <button
              className="welcome-send-btn"
              type="submit"
              disabled={(!input.trim() && !file) || isLoadingChat || isLoadingImage}
            >
              전송
            </button>
          </form>
        </div>
      ) : (
        <>
          <div className="message-list" ref={messageListRef}>
            {messages.map((msg, idx) => (
              <div key={idx} className={`message-row ${msg.role}`}>
                {msg.role === "assistant" && (
                  <div className="avatar assistant-avatar">AI</div>
                )}

                <div className={`message-bubble ${msg.role}-bubble`}>
                  {msg.type === "imagePreview" && msg.previewUrl && (
                    <div className="analysis-result">
                      <img
                        src={msg.previewUrl}
                        alt="Upload Preview"
                        className="uploaded-image"
                      />
                    </div>
                  )}

                  {msg.type === "imageAnalysis" && (
                    <div className="analysis-result">
                      {msg.resultData?.error ? (
                        <div className="error-msg">
                          ⚠️ {msg.resultData.error}
                        </div>
                      ) : (
                        msg.resultData && (
                          <div className="detection-info">
                            <p>
                              <strong>감지된 물체:</strong>{" "}
                              {msg.resultData.main_class}
                            </p>
                            <p>
                              <strong>확률:</strong>{" "}
                              {msg.resultData.confidence}%
                            </p>
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

                  {msg.content && (
                    <div className="markdown-content">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  )}

                  {msg.role === "assistant" && msg.content && (
                    <button
                      className="copy-btn"
                      onClick={() => handleCopy(msg.content)}
                    >
                      <FiCopy />
                    </button>
                  )}
                </div>
              </div>
            ))}
            {isLoadingChat && (
              <div className="message-row assistant">
                <div className="loading-dots">...</div>
              </div>
            )}
          </div>

          <form className="chat-input-form" onSubmit={handleSubmitFromForm}>
            {preview && (
              <div className="staged-image-preview">
                <img src={preview} alt="Preview" />
                <button
                  type="button"
                  onClick={() => {
                    setFile(null);
                    setPreview(null);
                  }}
                >
                  ×
                </button>
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
        </>
      )}
    </div>
  );
}

export default Chat;