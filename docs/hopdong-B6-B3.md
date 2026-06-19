# BIÊN BẢN CHỐT HỢP ĐỒNG API VÀ GIẢI PHÁP TÍCH HỢP — CORE BUSINESS (B6) & ACCESS GATE (B3)

Dựa trên quá trình đàm phán, hai nhóm B6 và B3 đã thống nhất bộ giải pháp kỹ thuật toàn diện nhằm đảm bảo tính toàn vẹn dữ liệu, khả năng chịu tải và trải nghiệm người dùng tại cổng.

---

## 1. Chống Quẹt Đúp Thẻ (Idempotency & Spam Control)
**Giải pháp kết hợp 2 lớp:**
- **Hardware Debounce tại B3:** Khi quẹt thẻ, cổng B3 tự khóa (Local Lockout) đọc thẻ đó trong 1.5 - 2s để chặn spam từ phần cứng.
- **Idempotency Layer tại B6:** B3 truyền kèm Header `Idempotency-Key` (Công thức: `SHA256(StudentID + DeviceID + RoundToMinute(Timestamp))`). B6 check key này trong Redis (TTL 5s). Nếu trùng, B6 trả về 200 OK (data cũ) hoặc 409 Conflict, tuyệt đối không trừ tiền / ghi log 2 lần.

## 2. Rớt Mạng Đứt Cáp (Offline Mode & Bulk Sync)
**Phân định trách nhiệm rõ ràng:**
- **Chế độ Offline:** B3 hỗ trợ tính năng lưu danh sách trắng (Local Whitelist Cache) đồng bộ hàng đêm. Khi rớt mạng, cổng có thể tự cấu hình Fail-open (mở bừa) hoặc Fail-closed (chỉ cho thẻ trong whitelist). Log được B3 ghi vào database cục bộ (SQLite).
- **Đồng bộ bù (Bulk Sync):** Khi có mạng lại, API `/events` của B6 BẮT BUỘC nhận payload dạng Mảng (Array).
  - B3 sẽ đẩy dữ liệu theo lô (Batch) từ 100-200 records/request.
  - Rate limit: B3 giới hạn tự bắn 5 Bulk Request/s, sử dụng thuật toán Exponential Backoff để chống DDoS hệ thống B6.

## 3. Trạng Thái Vật Lý Khác Trạng Thái Logic (Physical Passage)
**Kiểm soát bằng cảm biến (IR Sensors):**
- B6 trả kết quả `ALLOW`, cổng mở, bắt đầu đếm ngược Timeout (5 giây).
- Nếu cảm biến B3 báo sinh viên **chưa đi qua** trong 5s, cổng tự đóng lại.
- Ngay lập tức, B3 gọi API `POST /events` về B6 với `status: ACCESS_CANCELLED`, `reason: PHYSICAL_TIMEOUT_NO_PASSAGE`.
- Nhận được lệnh này, B6 rollback lại toàn bộ trạng thái (hoàn tiền, xóa trạng thái đã vào cổng) để dữ liệu kiểm toán chính xác 100%.

## 4. Kéo Dữ Liệu Khủng & Giới Hạn Tải (Pagination & Throttling)
- **Cơ chế Phân trang:** API `GET /access/logs/recent` của B3 bắt buộc dùng **Cursor-based Pagination** (trả về `next_cursor`), không dùng Limit/Offset để tránh sập database khi lùi về cuối dữ liệu.
- **Ngưỡng chịu tải:** Cụm Gate chịu tối đa 150 - 200 RPS.
- **Throttling của B3:** B3 sử dụng thuật toán Token Bucket, giới hạn riêng B6 chỉ được gọi tối đa 50 RPS khi kéo log. Vượt ngưỡng này, B3 trả `HTTP 429 Too Many Requests`. B6 có trách nhiệm tự động giảm tốc độ crawl dữ liệu (Crawler rate).

---
**Trạng thái:** ĐÃ CHỐT KÝ 🤝
