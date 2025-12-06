# backend/app/api/yolo_api.py

from fastapi import APIRouter, UploadFile, File
from pathlib import Path
from app.models.yolo_best_model import predict_image

router = APIRouter(prefix="/yolo", tags=["yolo"])

# 업로드된 이미지를 임시로 저장할 폴더
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/predict")
async def yolo_predict(file: UploadFile = File(...)):
    # 1) 파일을 서버 로컬에 저장
    save_path = UPLOAD_DIR / file.filename
    with open(save_path, "wb") as f:
        f.write(await file.read())

    # 2) YOLO 추론 실행
    result = predict_image(str(save_path))

    # 3) 결과 반환 (프론트에서 JSON으로 받음)
    return {"result": result}
