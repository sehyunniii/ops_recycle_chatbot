# backend/app/services/classification_service.py
import io
from PIL import Image
import torch
import torchvision.transforms as T
import torch.nn as nn
from torchvision.models import resnet50
import os

# (ResNet50_Dropout 클래스 정의...)
class ResNet50_Dropout(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.model = resnet50(weights="IMAGENET1K_V1")
        in_features = self.model.fc.in_features
        self.model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(in_features, num_classes)
        )
    def forward(self, x):
        return self.model(x)

class ModelWrapper:
    def __init__(self, model_path, device="cpu"):
        self.device = torch.device(device)
        self.num_classes = 24
        self.model = ResNet50_Dropout(self.num_classes).to(self.device)
        
        print(f"Loading model weights from: {model_path}")
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
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
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        x = self.transform(img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            out = self.model(x)
            probs = torch.nn.functional.softmax(out, dim=1)
            score, idx = torch.max(probs, dim=1)
            label = self.id2label[int(idx.item())]
            confidence = float(score.item())
            return label, confidence