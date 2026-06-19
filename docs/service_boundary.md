# Service Boundary — Access Gate (B3, Product B)

## 1. Thông tin service

| Mục | Giá trị |
|-----|---------|
| Tên service | `access-gate-b3` |
| Nhóm | B3 |
| Sản phẩm | Product B |
| Port mặc định | `3003` |
| OpenAPI | `openapi.yaml` |

## 2. Vai trò

Access Gate mô phỏng cổng kiểm soát ra/vào bằng RFID / mã sinh viên / nhân viên.

## 3. Provider — B3 cung cấp API cho ai?

| Consumer | Mục đích |
|----------|----------|
| RFID simulator / Front-end demo | Gửi sự kiện quẹt thẻ |
| Postman / Newman | Kiểm thử tích hợp |
| Admin (optional) | CRUD thẻ, xem log |

**API do B3 cung cấp:**

- `GET /health`
- `POST /api/v1/access/check`
- `GET /api/v1/access/logs`
- `GET /api/v1/cards/{card_id}`
- `POST /api/v1/cards`

## 4. Dependencies — B3 gọi service nào?

| Service | Nhóm | Hướng | Endpoint | Bắt buộc hợp đồng? |
|---------|------|-------|----------|-------------------|
| Core Business | **B6** | B3 → B6 | `POST /api/v1/events/access` | **CÓ — quan trọng nhất** |
| Analytics | **B5** | B3 → B5 | `POST /api/v1/ingest/access` | **CÓ** |
| Notification | B7 | Gián tiếp qua B6 | — | Không (B6 lo) |

## 5. Input / Output

### Input chính (`POST /api/v1/access/check`)

```json
{
  "card_id": "RFID-2026-001",
  "gate_id": "gate-main",
  "direction": "IN",
  "timestamp": "2026-05-02T07:30:00"
}
```

### Output chính

```json
{
  "access_granted": true,
  "reason": "Valid student card",
  "person_id": "SV001",
  "person_name": "Nguyen Van A",
  "person_type": "student",
  "gate_id": "gate-main",
  "direction": "IN",
  "event_id": "acc-20260502-abc12345",
  "checked_at": "2026-05-02T07:30:01Z"
}
```

## 6. In scope — B3 làm gì?

- Validate request quẹt thẻ
- Tra cứu thẻ trong DB nội bộ
- Quyết định `access_granted` tại cổng
- Ghi `access_logs`
- Gửi event sang **B6** và **B5**
- Trả response đồng bộ cho client

## 7. Out of scope — B3 KHÔNG làm gì?

| Việc | Service chịu trách nhiệm |
|------|--------------------------|
| Gửi Telegram/email | Notification (B7) qua Core (B6) |
| Kiểm tra chính sách phức tạp (ngoài giờ, nhiều lần bất thường) | Core Business (B6) |
| Báo cáo thống kê tổng hợp | Analytics (B5) |
| Phân tích AI camera | AI Vision (B4) |
| Nhận dữ liệu IoT | IoT Ingestion (B1) |

## 8. Luồng tích hợp

```text
Client / RFID
    → B3 Access Gate (check + log)
        → B6 Core Business (policy + cảnh báo)
            → B7 Notification (gián tiếp)
        → B5 Analytics (metric)
```

## 9. Quy tắc lỗi integration

Nếu B5 hoặc B6 tạm thời không phản hồi:

- B3 **vẫn trả response** cho client quẹt thẻ
- Ghi log `INTEGRATION ... failed`
- Không rollback access log đã lưu
