# MLPDR

Detection et reconnaissance de plaques marocaines avec YOLOv3.

Cette version du projet inclut:
- interface desktop PyQt5
- API Flask
- frontend React
- stack Docker (frontend + backend)

## Prerequis

- Python 3.11 recommande
- Node.js 20+
- Docker Desktop (optionnel)
- Poids YOLO dans `./weights`

## Lancement avec Docker

```bash
docker compose up --build -d
```

Acces:
- frontend: `http://localhost:5173`
- API: `http://localhost:5000`

Arret:

```bash
docker compose down
```

## Lancement local

### API Flask

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install --upgrade pip
pip install Flask numpy opencv-python Pillow pytesseract arabic-reshaper python-bidi requests
python api.py
```

### Frontend React

```bash
cd frontend
npm install
npm run dev
```

### GUI Desktop

```bash
.venv\Scripts\activate
pip install PyQt5
python main.py
```

## Poids attendus

- `./weights/detection/yolov3-detection_final.weights`
- `./weights/detection/yolov3-detection.cfg`
- `./weights/ocr/yolov3-ocr_final.weights`
- `./weights/ocr/yolov3-ocr.cfg`

Source des poids:
- https://github.com/HamzaEzzRa/MLPDR/releases/tag/v1.0.0-beta

## API

Endpoint:
- `POST /upload`

Form-data:
- `image` (obligatoire)
- `ocr_mode` (`trained` ou `tesseract`, optionnel)

Exemple:

```bash
curl -X POST "http://127.0.0.1:5000/upload" \
  -F "image=@./test_images/20200617_185301b_contrast.jpg" \
  -F "ocr_mode=trained"
```

## Troubleshooting rapide

- `weights` manquants: verifier le dossier `./weights`.
- Tesseract non trouve en local Windows: verifier `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- Port occupe (`5000`, `5173`): arreter le process ou changer le port.
- Docker indisponible: lancer Docker Desktop.

## Licence

MIT.