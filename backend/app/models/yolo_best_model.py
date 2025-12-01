# backend/app/models/yolo_best_model.py

from pathlib import Path
from ultralytics import YOLO

# 이 파일이 있는 폴더 기준으로 weights/recycle_best.pt 위치 찾기
BASE_DIR = Path(__file__).resolve().parent
WEIGHT_PATH = BASE_DIR / "weights" / "recycle_best.pt"

# 서버 시작할 때 한 번만 모델 로드
yolo_model = YOLO(str(WEIGHT_PATH))


def predict_image(image_path: str):
    """
    image_path: 로컬에 저장된 이미지 파일 경로
    return: YOLO 결과를 리스트(dict)로 반환
    """
    results = yolo_model(image_path)   # 결과 리스트
    r = results[0]

    outputs = []
    for box in r.boxes:
        cls_id = int(box.cls[0])
        cls_name = r.names[cls_id]     # class_0, class_1 ... (나중에 한글 이름 매핑 가능)
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()    # [x1, y1, x2, y2]

        outputs.append({
            "class_id": cls_id,
            "class_name": cls_name,
            "confidence": conf,
            "bbox": xyxy,
        })

    return outputs
