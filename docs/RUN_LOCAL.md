# Chạy Access Gate Service (B3) — Local & Docker

## Yêu cầu

- Python 3.11+
- Docker Desktop (nếu chạy bằng container)
- Postman hoặc Newman (kiểm thử)

## 1. Chạy local (SQLite — nhanh nhất)

```powershell
cd "d:\B3_Access Gate"

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env
python -m src.main
```

Service chạy tại: http://localhost:3003

- Health: http://localhost:3003/health
- Swagger UI: http://localhost:3003/docs
- OpenAPI JSON: http://localhost:3003/openapi.json

## 2. Test nhanh bằng curl

```powershell
curl http://localhost:3003/health

curl -X POST http://localhost:3003/api/v1/access/check `
  -H "Content-Type: application/json" `
  -d "{\"card_id\":\"RFID-2026-001\",\"gate_id\":\"gate-main\",\"direction\":\"IN\",\"timestamp\":\"2026-05-02T07:30:00\"}"
```

## 3. Chạy bằng Docker Compose (PostgreSQL)

```powershell
cd "d:\B3_Access Gate"
copy .env.example .env
docker compose up --build -d
docker compose ps
curl http://localhost:3003/health
```

Dừng service:

```powershell
docker compose down
```

## 4. Mock B6 và B5 để test integration

Mở 2 terminal, chạy mock server:

```powershell
cd "d:\B3_Access Gate"
.\.venv\Scripts\Activate.ps1
python scripts/mock_core_business.py
```

```powershell
cd "d:\B3_Access Gate"
.\.venv\Scripts\Activate.ps1
python scripts/mock_analytics.py
```

Sau đó gọi lại `POST /api/v1/access/check` — log sẽ hiện `INTEGRATION ... success`.

## 5. Postman / Newman

Import:

- `postman/access_gate.postman_collection.json`
- `postman/local.postman_environment.json`

Chạy Newman:

```powershell
newman run postman/access_gate.postman_collection.json `
  -e postman/local.postman_environment.json `
  --reporters cli,json `
  --reporter-json-export evidence/newman_report.json
```

## 6. Dữ liệu mẫu (seed cards)

| card_id | Trạng thái | Kết quả test |
|---------|------------|--------------|
| RFID-2026-001 | active student | access_granted = true |
| RFID-2026-999 | expired | access_granted = false |
| RFID-2026-888 | blocked | access_granted = false |
| RFID-UNKNOWN | không tồn tại | access_granted = false |

## 7. Biến môi trường quan trọng

Xem `.env.example`. Khi tích hợp Product B:

```env
CORE_BUSINESS_URL=http://localhost:3006
ANALYTICS_URL=http://localhost:3005
```

Chi tiết hợp đồng với B5/B6: xem `HOP_DONG_API.md`.
