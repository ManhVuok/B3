# Hợp đồng API — Access Gate (B3) cần thống nhất với nhóm nào?

> **Tóm tắt nhanh:** Nhóm B3 chỉ cần làm hợp đồng **trực tiếp** với **2 nhóm Product B**:
> 1. **B6 — Core Business** (bắt buộc)
> 2. **B5 — Analytics** (bắt buộc)
>
> **Không** cần hợp đồng trực tiếp với B7 Notification (B6 sẽ gọi B7).

---

## 1. Bảng tổng hợp — Product B

| Nhóm | Service | Cần hợp đồng với B3? | Vai trò liên quan B3 |
|------|---------|----------------------|----------------------|
| B1 | IoT Ingestion | **Không bắt buộc** | Luồng cảm biến riêng, không qua cổng RFID |
| B2 | Camera Stream | **Không bắt buộc** | Luồng camera riêng |
| **B3** | **Access Gate** | — | **Service của bạn** |
| B4 | AI Vision | **Không bắt buộc** | Không liên quan cổng ra/vào |
| **B5** | **Analytics** | **CÓ — Bắt buộc** | B3 **gửi** metric access sang B5 |
| **B6** | **Core Business** | **CÓ — Bắt buộc** | B3 **gửi** access event sang B6 |
| B7 | Notification | **Không trực tiếp** | B6 gọi B7 khi có cảnh báo |

### Lưu ý quan trọng

- Chỉ thống nhất với nhóm **Product B** (B5, B6).
- **Không** gọi nhóm Product A (A5, A6…) vì là 2 sản phẩm song song.
- Hai nhóm cùng loại service (ví dụ A3 và B3 đều là Access Gate) **có thể khác stack**, nhưng **trong Product B** phải thống nhất payload với B5/B6.

---

## 2. Hợp đồng 1 — B3 → B6 Core Business (QUAN TRỌNG NHẤT)

### Ai chủ động?

- **B3 (Access Gate)** = **Provider event** — gửi đi
- **B6 (Core Business)** = **Consumer** — nhận event, kiểm tra chính sách, có thể gọi B7

### Endpoint đề xuất (thống nhất với B6)

```http
POST {CORE_BUSINESS_URL}/api/v1/events/access
Content-Type: application/json
```

Ví dụ local:

```text
POST http://localhost:3006/api/v1/events/access
```

### Request body — B3 gửi sang B6

File tham chiếu trong repo: `src/schemas.py` → `CoreBusinessAccessEvent`

```json
{
  "event_id": "acc-20260502-abc12345",
  "card_id": "RFID-2026-001",
  "person_id": "SV001",
  "person_name": "Nguyen Van A",
  "person_type": "student",
  "gate_id": "gate-main",
  "direction": "IN",
  "access_granted": true,
  "reason": "Valid student card",
  "timestamp": "2026-05-02T07:30:00",
  "source_service": "access-gate-b3",
  "product": "product-b"
}
```

### Response mong đợi từ B6 (đề xuất — hỏi B6 xác nhận)

```json
{
  "received": true,
  "event_id": "acc-20260502-abc12345",
  "policy_result": "NORMAL",
  "alert_required": false
}
```

HTTP status: `200` hoặc `201`

### Cần hỏi nhóm B6 khi họp hợp đồng

1. URL chính xác và port (mặc định gợi ý `3006`)
2. Path có đúng `/api/v1/events/access` không?
3. Field nào **bắt buộc** / **optional**?
4. B6 có cần `Authorization` header không?
5. B6 trả về schema response thế nào?
6. Khi B6 phát hiện bất thường, B6 tự gọi B7 — B3 không cần biết chi tiết

### Biến môi trường B3

```env
CORE_BUSINESS_URL=http://localhost:3006
CORE_BUSINESS_EVENT_PATH=/api/v1/events/access
```

---

## 3. Hợp đồng 2 — B3 → B5 Analytics (BẮT BUỘC)

### Ai chủ động?

- **B3 (Access Gate)** = **Provider dữ liệu** — gửi metric
- **B5 (Analytics)** = **Consumer** — ingest và thống kê

### Endpoint đề xuất (thống nhất với B5)

```http
POST {ANALYTICS_URL}/api/v1/ingest/access
Content-Type: application/json
```

Ví dụ local:

```text
POST http://localhost:3005/api/v1/ingest/access
```

### Request body — B3 gửi sang B5

File tham chiếu: `src/schemas.py` → `AnalyticsAccessEvent`

```json
{
  "event_id": "acc-20260502-abc12345",
  "gate_id": "gate-main",
  "direction": "IN",
  "access_granted": true,
  "person_type": "student",
  "timestamp": "2026-05-02T07:30:00",
  "source_service": "access-gate-b3",
  "product": "product-b"
}
```

### Response mong đợi từ B5 (đề xuất — hỏi B5 xác nhận)

```json
{
  "received": true,
  "event_id": "acc-20260502-abc12345"
}
```

HTTP status: `200` hoặc `202`

### Cần hỏi nhóm B5 khi họp hợp đồng

1. URL và port (gợi ý `3005`)
2. Path ingest có đúng `/api/v1/ingest/access` không?
3. B5 cần thêm field nào (ví dụ `card_id`, `person_id`)?
4. Format `timestamp`: ISO 8601 có timezone không?
5. B5 có hỗ trợ batch (nhiều event một request) không — MVP thường **không**

### Biến môi trường B3

```env
ANALYTICS_URL=http://localhost:3005
ANALYTICS_INGEST_PATH=/api/v1/ingest/access
```

---

## 4. Không cần hợp đồng trực tiếp — B7 Notification

Luồng theo đề bài:

```text
B3 → B6 → B7
```

- B3 **không** gọi Telegram/email
- Khi access bất thường, **B6** quyết định và gọi **B7**
- B3 chỉ cần **biết luồng** để trình bày demo, không cần openapi riêng với B7

---

## 5. Hợp đồng API của chính B3 — ai gọi B3?

Các nhóm khác **có thể** gọi B3 nếu demo tích hợp chung, nhưng **không bắt buộc** theo luồng đề bài:

| Nhóm | Gọi B3? | Ghi chú |
|------|---------|---------|
| B6 | Thường **không** gọi ngược B3 | B6 nhận event từ B3 |
| B5 | **Không** gọi ngược B3 | B5 chỉ ingest |
| Front-end nhóm B3 | **Có** | Demo quẹt thẻ |
| Giảng viên / Postman | **Có** | Nghiệm thu |

**OpenAPI của B3** nằm ở file `openapi.yaml` — đây là hợp đồng **public** mà nhóm B3 publish cho lớp.

---

## 6. Checklist họp hợp đồng với B5 và B6

Gửi cho 2 nhóm file này + `openapi.yaml` + payload mẫu ở trên.

```text
[ ] Xác nhận URL + port local/Docker
[ ] Xác nhận path endpoint
[ ] Xác nhận JSON schema request (copy từ repo B3)
[ ] Xác nhận JSON schema response
[ ] Xác nhận HTTP status code
[ ] Xác nhận có auth header không
[ ] Test 1 request thật Postman → pass
[ ] Ghi lại version hợp đồng (v1.0) và ngày thống nhất
```

---

## 7. Mock khi B5/B6 chưa xong

Repo B3 vẫn chạy được. Khi B6/B5 chưa sẵn sàng:

1. Log sẽ ghi `INTEGRATION ... failed` — vẫn hợp lệ cho demo MVP
2. Dùng **Postman Mock Server** hoặc chạy mock đơn giản:

```bash
# Ví dụ mock B6 bằng Python (chạy terminal riêng)
python -c "
from fastapi import FastAPI
import uvicorn
app = FastAPI()
@app.post('/api/v1/events/access')
def receive_event(payload: dict):
    print('B6 received:', payload)
    return {'received': True, 'event_id': payload.get('event_id')}
uvicorn.run(app, host='0.0.0.0', port=3006)
"
```

3. Set `.env`:
   ```env
   CORE_BUSINESS_URL=http://localhost:3006
   ANALYTICS_URL=http://localhost:3005
   ```

---

## 8. Mẫu tin nhắn gửi nhóm B6 / B5

```text
Chào nhóm B6/B5 (Product B),

Nhóm B3 (Access Gate) gửi draft hợp đồng integration:

- B3 gọi POST /api/v1/events/access (gửi B6)
  hoặc POST /api/v1/ingest/access (gửi B5)

Payload mẫu: (dán JSON ở trên)

Nhờ nhóm xác nhận:
1. URL + path
2. Field bắt buộc
3. Response mẫu

Repo B3: [link github]
OpenAPI B3: openapi.yaml

Cảm ơn nhóm!
```

---

## 9. Tóm tắt 1 câu cho báo cáo

> **Nhóm B3 cung cấp API kiểm soát ra/vào (`openapi.yaml`), đồng thời là consumer gọi sang Core Business (B6) và Analytics (B5) theo hợp đồng event đã thống nhất trong Product B.**
