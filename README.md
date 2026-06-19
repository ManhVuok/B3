# Access Gate Service — Nhóm B3 (Product B)

Smart Campus Operations Platform — FIT4110  
Service kiểm soát ra/vào bằng RFID / mã sinh viên.

## Bắt đầu nhanh

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m src.main
```

Mở http://localhost:3003/docs

Chi tiết: [RUN_LOCAL.md](./RUN_LOCAL.md)

## Hợp đồng API — cần thống nhất với nhóm nào?

| Nhóm | Service | Bắt buộc? |
|------|---------|-----------|
| **B6** | Core Business | **CÓ** — B3 gửi access event |
| **B5** | Analytics | **CÓ** — B3 gửi metric |
| B7 | Notification | Không trực tiếp (qua B6) |
| B1, B2, B4 | IoT / Camera / AI | Không bắt buộc |

Chi tiết đầy đủ: **[HOP_DONG_API.md](./HOP_DONG_API.md)**

## Artefact nghiệm thu

| File | Mô tả |
|------|-------|
| `openapi.yaml` | Hợp đồng API public của B3 |
| `service_boundary.md` | Ranh giới dịch vụ |
| `HOP_DONG_API.md` | Hợp đồng với B5, B6 |
| `postman/` | Collection kiểm thử |
| `Dockerfile` + `docker-compose.yml` | Đóng gói Docker |
| `evidence/` | Test report, log, screenshot |

## Cấu trúc

```text
src/                  # FastAPI source
openapi.yaml          # API contract
HOP_DONG_API.md       # Integration contracts
scripts/              # Mock B5, B6
postman/              # Postman tests
```

Hướng dẫn chi tiết triển khai: [HUONG_DAN_TRIEN_KHAI.md](./HUONG_DAN_TRIEN_KHAI.md)
