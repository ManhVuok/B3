# Changelog - Access Gate (B3)

Tất cả những thay đổi quan trọng về API và cấu trúc dữ liệu của service Access Gate sẽ được ghi lại ở đây để các nhóm liên quan (B5, B6) tiện theo dõi.

## [1.0.0] - 2026-06-17

### Thêm mới (Added)
- Bổ sung Security Scheme (X-API-Key) vào toàn bộ `openapi.yaml`.
- Các request tới Access Gate nay phải có header `X-API-Key: DVKN2026-SECRET-KEY` (Môi trường local).

### Thay đổi (Changed)
- Thống nhất payload gửi sang B6 (`POST /api/v1/events/access`) và B5 (`POST /api/v1/ingest/access`) theo `HOP_DONG_API.md`.

## [0.1.0] - 2026-05-30

### Khởi tạo (Init)
- Khởi tạo service Access Gate với các API: `/api/v1/access/check`, `/api/v1/access/logs`, `/api/v1/cards/{card_id}`.
- Định nghĩa OpenAPI Contract ban đầu.
