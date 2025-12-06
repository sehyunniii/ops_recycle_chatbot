# backend/app/services/classification_service.py

import io
from PIL import Image
from ultralytics import YOLO
import torch

class ModelWrapper:
    def __init__(self, model_path, device="cpu"):
        """
        YOLO 모델 기반 분류기
        """
        self.device = device

        print(f"[ModelWrapper] Loading YOLO model from: {model_path}")
        self.model = YOLO(model_path)   # YOLO 모델 로드

        # 🔴 [삭제] 수동으로 적은 딕셔너리는 위험합니다! 지우세요.
        # self.id2label = {
        #    0: "01_ClearPET", 1: "02_OtherPlastic", ...
        # }

        # 🟢 [수정] 모델이 가지고 있는 진짜 이름을 가져옵니다.
        # best.pt 파일 안에 이미 클래스 이름들이 저장되어 있습니다.
        self.id2label = self.model.names 
        print(f"✅ 모델 클래스 매핑 로드 완료: {self.id2label}")

    def predict_image_bytes(self, img_bytes: bytes):
        """
        업로드된 이미지를 YOLO 모델에 넣고 가장 confidence 높은 클래스를 반환
        """
        # 이미지 변환
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        # 예측 실행
        results = self.model(img)
        
        # 결과 박스 확인
        boxes = results[0].boxes

        if boxes is None or len(boxes) == 0:
            return None, 0.0

        # 가장 확률 높은 객체 선택
        top_idx = torch.argmax(boxes.conf).item()
        
        # 클래스 ID와 확률 추출
        cls_id = int(boxes.cls[top_idx].item())
        conf = float(boxes.conf[top_idx].item())

        # 🟢 [수정] 모델 내부 정보(self.id2label)를 이용해 이름 변환
        # 이제 모델이 생각하는 것과 코드가 출력하는 것이 100% 일치합니다.
        label = self.id2label[cls_id]

        return label, conf