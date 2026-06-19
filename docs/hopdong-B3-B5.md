# BIÊN BẢN HỢP ĐỒNG API — ACCESS GATE (B3) & ANALYTICS (B5)

## 1. Giới thiệu
Biên bản này thống nhất cấu trúc dữ liệu và phương thức giao tiếp giữa **Access Gate (B3)** và **Analytics (B5)**. 
B3 đóng vai trò là **Provider (gửi dữ liệu)** và B5 đóng vai trò là **Consumer (nhận dữ liệu để thống kê)**.

## 2. API Tích hợp (B3 gọi B5)

Mỗi khi có lượt ra/vào tại cổng (thành công hoặc thất bại), B3 sẽ gửi một HTTP POST request đến hệ thống của B5.

- **Giao thức:** HTTP POST
- **Endpoint đề xuất:** `/api/v1/ingest/access` (Nhóm B5 vui lòng xác nhận hoặc cung cấp path chính xác).

### 2.1 Request Payload (B3 gửi B5)

Dữ liệu được gửi dưới dạng JSON (`Content-Type: application/json`):

```json
{
  "event_id": "acc-20260502-abc12345",
  "gate_id": "gate-main",
  "direction": "IN",
  "access_granted": true,
  "person_type": "student",
  "timestamp": "2026-05-02T07:30:00Z",
  "source_service": "access-gate-b3",
  "product": "product-b"
}
```

**Chi tiết các trường (Fields):**
- `event_id` (string): Mã định danh duy nhất của lượt quẹt thẻ.
- `gate_id` (string): ID của cổng vật lý (vd: `gate-main`, `gate-lab`).
- `direction` (enum): Hướng di chuyển (`IN` hoặc `OUT`).
- `access_granted` (boolean): `true` nếu được qua cổng, `false` nếu bị từ chối.
- `person_type` (enum): Loại người dùng (`student`, `staff`, `guest` hoặc `null` nếu thẻ không tồn tại).
- `timestamp` (string): Thời gian quẹt thẻ (định dạng ISO 8601 UTC).
- `source_service` (string): Mặc định là `"access-gate-b3"`.
- `product` (string): Mặc định là `"product-b"`.

*(Nhóm B5 vui lòng xem qua các trường này. Nếu B5 cần B3 cung cấp thêm trường nào để phục vụ vẽ biểu đồ thống kê, vui lòng phản hồi lại).*

### 2.2 Response mong đợi từ B5

B3 mong đợi B5 trả về HTTP Status `200 OK` hoặc `202 Accepted` với JSON như sau:

```json
{
  "received": true,
  "event_id": "acc-20260502-abc12345"
}
```

## 3. Các yêu cầu khác cần B5 xác nhận
1. **URL và Port:** Xin cung cấp URL gốc (Base URL) và Port của hệ thống B5 khi chạy local và chạy Docker.
2. **Cơ chế Batch/Bulk:** Hiện tại B3 đang gửi từng sự kiện (Real-time). B5 có yêu cầu B3 gom nhiều sự kiện thành một mảng (Array) để gửi 1 lần (Bulk Sync) giống nhóm B6 không?
3. **Throttling:** Hệ thống B5 có yêu cầu Rate Limit (Giới hạn số request/giây) từ B3 không?

---
**Trạng thái:** CHỜ B5 XÁC NHẬN ⏳
