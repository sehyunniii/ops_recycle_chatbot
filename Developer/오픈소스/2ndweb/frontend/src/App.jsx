// src/App.jsx
import "./App.css";
import Chat from "./Chat";
import "./Chat.css";

function App() {
  return (
    <div className="app-layout">
      
      {/* ⭐️ (수정) 왼쪽 사이드바 내용 변경 */}
      <div className="sidebar">
        <h2>분리수거 가이드</h2>
        
        <p className="sidebar-intro">
          채팅창에 이미지를 올리거나 질문을 입력해 
          정확한 배출 방법을 확인하세요.
        </p>

        {/* 1. 핵심 원칙 */}
        <div className="sidebar-section">
          <h3>분리배출 4대 원칙</h3>
          <ul className="principles-list">
            <li><strong>비운다:</strong> 용기 안의 내용물을 깨끗이 비우기</li>
            <li><strong>헹군다:</strong> 이물질, 음식물 등은 물로 헹구기</li>
            <li><strong>분리한다:</strong> 라벨, 뚜껑 등 다른 재질은 분리하기</li>
            <li><strong>섞지 않는다:</strong> 종류별, 재질별로 구분해 배출하기</li>
          </ul>
        </div>

        {/* 2. 자주 헷갈리는 품목 */}
        <div className="sidebar-section">
          <h3>자주 헷갈리는 품목 (FAQ)</h3>
          <ul className="faq-list">
            <li><strong>깨진 유리:</strong> <span>재활용 불가. 신문지에 싸서 종량제 봉투 배출.</span></li>
            <li><strong>컵라면 용기:</strong> <span>스티로폼(깨끗하면)은 재활용, 종이컵(코팅)은 일반쓰레기.</span></li>
            <li><strong>영수증/전표:</strong> <span>특수 코팅 종이. 재활용 불가. 일반쓰레기.</span></li>
            <li><strong>아이스팩:</strong> <span>물(Water)로 된 팩은 물을 버리고 비닐 분리배출, 고흡수성 수지(젤)는 뜯지 말고 종량제 봉투.</span></li>
            <li><strong>칫솔/볼펜:</strong> <span>여러 재질이 혼합되어 재활용 불가. 일반쓰레기.</span></li>
          </ul>
        </div>

      </div>

      {/* 3. 오른쪽 메인 콘텐츠 (챗봇) */}
      <Chat />

    </div>
  );
}

export default App;