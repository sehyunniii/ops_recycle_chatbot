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

        # YOLO 모델이 분류하는 클래스 이름 매핑
        self.id2label = {
            0: "01_ClearPET", 1: "02_OtherPlastic", 2: "03_Vinyl", 3: "04_Styrofoam",
            4: "05_Paper", 5: "06_PaperCarton", 6: "07_GlassBottle", 7: "08_CanMetal",
            8: "09_DirtyContainer", 9: "10_CoatedPaper", 10: "11_SmallPlastic",
            11: "12_OtherPackaging", 12: "13_Ceramic", 13: "14_RubberTube",
            14: "15_OtherGlass", 15: "16_CD_DVD", 16: "17_CosmeticContainer",
            17: "18_IcePack", 18: "19_Toy", 19: "20_WoodHousehold",
            20: "21_Appliance", 21: "22_Textile", 22: "23_Battery", 23: "24_FluorescentLamp"
        }

    def predict_image_bytes(self, img_bytes: bytes):
        """
        업로드된 이미지를 YOLO 모델에 넣고 가장 confidence 높은 클래스를 반환
        """
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

        results = self.model(img)

        boxes = results[0].boxes

        # 감지된 객체가 하나도 없다면
        if boxes is None or len(boxes) == 0:
            return None, 0.0

        # 가장 confidence 높은 box 선택
        top_idx = torch.argmax(boxes.conf).item()

        cls_id = int(boxes.cls[top_idx].item())
        conf = float(boxes.conf[top_idx].item())

        # YOLO 내부 이름이 아닌, 우리가 관리하는 id2label 사용
        label = self.id2label.get(cls_id, "Unknown")

        return label, conf