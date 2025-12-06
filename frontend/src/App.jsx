// src/App.jsx
import { useEffect, useState } from "react";
import "./App.css";
import Chat from "./Chat";
import "./Chat.css";

const META_KEY = "ecobot_conversations_meta_v1";

const generateConversationId = () => {
  const g = globalThis;
  if (g.crypto && typeof g.crypto.randomUUID === "function") {
    return g.crypto.randomUUID();
  }
  return `conv_${Date.now()}_${Math.random().toString(16).slice(2)}`;
};

const createNewConversation = () => {
  const id = generateConversationId();
  return {
    id,
    title: "새 대화",
    createdAt: Date.now(),
    storageKey: `chat_history_${id}`,
  };
};

const loadConversationMeta = () => {
  try {
    const saved = localStorage.getItem(META_KEY);
    if (saved) {
      return JSON.parse(saved); 
    }

    const legacy = localStorage.getItem("chat_history");
    if (legacy) {
      return [
        {
          id: "legacy-1",
          title: "기존 대화",
          createdAt: Date.now(),
          storageKey: "chat_history",
        },
      ];
    }

    return [];
  } catch (e) {
    console.error("대화 메타데이터 로드 오류:", e);
    return [];
  }
};

function App() {
  const [conversations, setConversations] = useState(() => {
    const meta = loadConversationMeta();
    if (meta.length === 0) {
      const first = createNewConversation();
      return [first];
    }
    return meta;
  });

  const [activeId, setActiveId] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    if (!activeId && conversations.length > 0) {
      setActiveId(conversations[0].id);
    }
  }, [activeId, conversations]);

  useEffect(() => {
    try {
      localStorage.setItem(META_KEY, JSON.stringify(conversations));
    } catch (e) {
      console.error("대화 메타데이터 저장 오류:", e);
    }
  }, [conversations]);

  const activeConversation =
    conversations.find((c) => c.id === activeId) || null;

  const handleNewChat = () => {
    const newConv = createNewConversation();
    setConversations((prev) => [newConv, ...prev]);
    setActiveId(newConv.id);
  };

  const handleSelectConversation = (id) => {
    setActiveId(id);
  };

  const handleDeleteConversation = (id) => {
    const convToDelete = conversations.find((c) => c.id === id);
    if (!convToDelete) return;

    if (!window.confirm("이 대화 기록을 삭제하시겠습니까?")) return;

    try {
      localStorage.removeItem(convToDelete.storageKey);
    } catch (e) {
      console.error("대화 삭제 중 localStorage 오류:", e);
    }

    setConversations((prev) => prev.filter((c) => c.id !== id));

    if (activeId === id) {
      const remaining = conversations.filter((c) => c.id !== id);
      setActiveId(remaining[0]?.id || null);
    }
  };

  const handleDeleteAll = () => {
    if (!conversations.length) return;
    if (!window.confirm("모든 채팅 기록을 삭제하시겠습니까?")) return;

    try {
      conversations.forEach((c) => {
        localStorage.removeItem(c.storageKey);
      });
      localStorage.removeItem(META_KEY);
    } catch (e) {
      console.error("전체 삭제 중 localStorage 오류:", e);
    }

    setConversations([]);
    setActiveId(null);
  };

  const handleUpdateTitle = (id, newTitle) => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === id ? { ...conv, title: newTitle } : conv
      )
    );
  };

  const toggleSidebar = () => {
    setIsSidebarOpen((prev) => !prev);
  };

  return (
    <div className="app-layout">
      <button className="mobile-tab-btn" onClick={toggleSidebar}>
        ≡
      </button>

      <aside
        className={
          "sidebar " + (isSidebarOpen ? "sidebar-open" : "sidebar-closed")
        }
      >
        <div className="sidebar-header">
          <div className="sidebar-logo-row">
            <img
              src="/chatbot_logo.png"
              alt="EcoBot 로고"
              className="sidebar-logo-image"
            />
            <div className="sidebar-logo-text">
              <div className="sidebar-logo-title">EcoBot</div>
              <div className="sidebar-logo-sub">분리수거 도우미 챗봇</div>
            </div>
          </div>

          <button className="sidebar-new-chat-btn" onClick={handleNewChat}>
            + 새 채팅
          </button>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-header">
            <h3>채팅 기록</h3>
            {conversations.length > 0 && (
              <button
                className="sidebar-clear-all-btn"
                onClick={handleDeleteAll}
              >
                전체 삭제
              </button>
            )}
          </div>

          {conversations.length === 0 ? (
            <p className="sidebar-empty">저장된 채팅 기록이 없습니다.</p>
          ) : (
            <div className="chat-history-list">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={
                    "chat-history-item" +
                    (conv.id === activeId ? " chat-history-item-active" : "")
                  }
                >
                  <button
                    className="chat-history-title"
                    onClick={() => handleSelectConversation(conv.id)}
                  >
                    {conv.title || "새 대화"}
                  </button>
                  <button
                    className="chat-history-delete"
                    onClick={() => handleDeleteConversation(conv.id)}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <hr className="sidebar-divider" />

        <div className="sidebar-section">
          <h2>분리배출 4대 원칙</h2>
          <p className="sidebar-intro">
            채팅창에 이미지를 올리거나 질문을 입력해
            정확한 배출 방법을 확인하세요.
          </p>

          <ul className="principles-list">
            <li>
              <strong>비운다:</strong> 용기 안의 내용물을 깨끗이 비우기
            </li>
            <li>
              <strong>헹군다:</strong> 이물질, 음식물 등은 물로 헹구기
            </li>
            <li>
              <strong>분리한다:</strong> 라벨, 뚜껑 등 다른 재질은 분리하기
            </li>
            <li>
              <strong>섞지 않는다:</strong> 종류별, 재질별로 구분해 배출하기
            </li>
          </ul>
        </div>
      </aside>

      <div className="chat-main">
        {activeConversation && (
          <Chat
            storageKey={activeConversation.storageKey}
            onNewChat={handleNewChat}
            onUpdateTitle={(newTitle) =>
              handleUpdateTitle(activeConversation.id, newTitle)
            }
          />
        )}
      </div>
    </div>
  );
}

export default App;
