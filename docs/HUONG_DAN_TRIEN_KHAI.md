# Hướng dẫn chi tiết — Access Gate Service (Nhóm B3, Product B)

> **Học phần:** FIT4110 — Dịch vụ kết nối và Công nghệ nền tảng  
> **Đề tài:** Xây dựng dịch vụ kiểm soát ra/vào (Access Gate Service)  
> **Sản phẩm:** Product B — Smart Campus Operations Platform

---

## Mục lục

1. [Tổng quan bài tập](#1-tổng-quan-bài-tập)
2. [Vai trò Access Gate trong hệ thống](#2-vai-trò-access-gate-trong-hệ-thống)
3. [Service boundary — ranh giới dịch vụ](#3-service-boundary--ranh-giới-dịch-vụ)
4. [Thiết kế API (hợp đồng bắt buộc)](#4-thiết-kế-api-hợp-đồng-bắt-buộc)
5. [Kiến trúc và công nghệ đề xuất](#5-kiến-trúc-và-công-nghệ-đề-xuất)
6. [Cấu trúc thư mục dự án](#6-cấu-trúc-thư-mục-dự-án)
7. [Triển khai từng bước](#7-triển-khai-từng-bước)
8. [Kết nối với service khác (Product B)](#8-kết-nối-với-service-khác-product-b)
9. [Docker và Docker Compose](#9-docker-và-docker-compose)
10. [Kiểm thử Postman / Newman](#10-kiểm-thử-postman--newman)
11. [Artefact bắt buộc phải nộp](#11-artefact-bắt-buộc-phải-nộp)
12. [Demo Pack và nghiệm thu](#12-demo-pack-và-nghiệm-thu)
13. [Checklist trước khi nộp](#13-checklist-trước-khi-nộp)
14. [Lộ trình làm việc theo tuần (gợi ý)](#14-lộ-trình-làm-việc-theo-tuần-gợi-ý)

---

## 1. Tổng quan bài tập

Nhóm **B3** xây dựng **Access Gate Service** — service mô phỏng cổng kiểm soát ra/vào bằng:

- Thẻ RFID
- Mã sinh viên / mã nhân viên
- QR code (tùy chọn mở rộng)

Service **không chỉ chạy trên máy nhóm B3**. Service phải:

| Yêu cầu | Ý nghĩa |
|---------|---------|
| Có `openapi.yaml` | Hợp đồng API thống nhất với nhóm khác |
| Có test Postman/Newman | Chứng minh API hoạt động đúng |
| Có Dockerfile | Đóng gói, chạy được trên máy người khác |
| Có `docker-compose.yml` (nếu dùng DB) | Chạy cùng database phụ trợ |
| Kết nối ≥ 1 service khác | Gửi/nhận dữ liệu thật qua HTTP |
| Có minh chứng vận hành | Log, screenshot, test report, video demo |

**Lưu ý quan trọng:** Giảng viên **không chấm nặng giao diện**. Front-end có thể có để demo quẹt thẻ, nhưng **không thay thế** OpenAPI, Postman, Docker và tích hợp.

---

## 2. Vai trò Access Gate trong hệ thống

### 2.1 Luồng dữ liệu tổng quát

```text
RFID Reader / Form nhập mã / QR Scanner (mô phỏng)
        ↓
Access Gate Service (B3)          ← nhóm bạn
        ↓
Core Business Service (B6)        ← kiểm tra chính sách, quyết định cảnh báo
        ↓
Notification Service (B7)         ← gửi cảnh báo (gián tiếp qua Core)

Access Gate Service (B3)
        ↓
Analytics Service (B5)            ← thống kê lượt vào/ra
```

### 2.2 Nhiệm vụ cụ thể của nhóm B3

1. **Nhận sự kiện** quẹt thẻ hoặc nhập mã tại cổng.
2. **Tra cứu người dùng** (thẻ hợp lệ, sinh viên/nhân viên còn hiệu lực).
3. **Quyết định tạm thời** `access_granted` tại cổng (cho phép / từ chối + lý do).
4. **Ghi log ra/vào** vào database nội bộ.
5. **Gửi event sang Core Business (B6)** để kiểm tra chính sách nâng cao (ví dụ: vào ngoài giờ, nhiều lần liên tiếp).
6. **Gửi dữ liệu sang Analytics (B5)** để tổng hợp metric (lượt IN/OUT, cổng nào bận nhất…).

### 2.3 Dữ liệu mẫu theo đề bài

**Đầu vào:**

```json
{
  "card_id": "RFID-2026-001",
  "gate_id": "gate-main",
  "direction": "IN",
  "timestamp": "2026-05-02T07:30:00"
}
```

**Đầu ra mong đợi:**

```json
{
  "access_granted": true,
  "reason": "Valid student card",
  "person_id": "SV001"
}
```

---

## 3. Service boundary — ranh giới dịch vụ

Tạo file `service_boundary.md` (bắt buộc). Nội dung gợi ý:

### 3.1 Access Gate **làm gì**

- Nhận request từ thiết bị RFID mô phỏng, Postman, hoặc front-end demo.
- Validate dữ liệu đầu vào (`card_id`, `gate_id`, `direction`, `timestamp`).
- Tra cứu thông tin thẻ/người dùng trong DB nội bộ.
- Trả response đồng bộ cho client: cho phép hay từ chối.
- Lưu access log (ai, cổng nào, IN/OUT, kết quả, thời gian).
- Gọi **Core Business (B6)** sau mỗi sự kiện hợp lệ.
- Gọi **Analytics (B5)** để cung cấp dữ liệu thống kê.

### 3.2 Access Gate **không làm gì**

- **Không** gửi Telegram/email trực tiếp → việc đó thuộc **Notification (B7)** qua **Core (B6)**.
- **Không** phân tích AI hình ảnh → thuộc **AI Vision (B4)**.
- **Không** quản lý toàn bộ chính sách campus → Core Business quyết định cảnh báo phức tạp.
- **Không** tạo báo cáo tổng hợp cuối cùng → Analytics (B5) làm.

### 3.3 Actor

| Actor | Vai trò |
|-------|---------|
| RFID Reader (mô phỏng) | Gửi sự kiện quẹt thẻ |
| Front-end demo (optional) | Form quẹt thẻ / chọn cổng |
| Postman/Newman | Kiểm thử tích hợp |
| Core Business (B6) | Consumer — nhận access event |
| Analytics (B5) | Consumer — nhận metric event |
| Admin (optional) | CRUD thẻ, xem log qua API |

---

## 4. Thiết kế API (hợp đồng bắt buộc)

File `openapi.yaml` là **hợp đồng chính thức**. Các nhóm Product B phải thống nhất payload khi gọi B5, B6.

### 4.1 Endpoint tối thiểu (MVP)

| Method | Path | Mô tả |
|--------|------|-------|
| `GET` | `/health` | Health check cho Docker / demo |
| `POST` | `/api/v1/access/check` | Xử lý sự kiện quẹt thẻ / nhập mã |
| `GET` | `/api/v1/access/logs` | Xem lịch sử ra/vào (phân trang) |
| `GET` | `/api/v1/cards/{card_id}` | Tra cứu thẻ (optional nhưng hữu ích demo) |
| `POST` | `/api/v1/cards` | Tạo thẻ mới (seed dữ liệu demo) |

### 4.2 Request/Response chuẩn — `POST /api/v1/access/check`

**Request body:**

```json
{
  "card_id": "RFID-2026-001",
  "gate_id": "gate-main",
  "direction": "IN",
  "timestamp": "2026-05-02T07:30:00"
}
```

**Validation:**

| Field | Rule |
|-------|------|
| `card_id` | Bắt buộc, string, không rỗng |
| `gate_id` | Bắt buộc, ví dụ: `gate-main`, `gate-lab` |
| `direction` | Bắt buộc, enum: `IN` hoặc `OUT` |
| `timestamp` | Bắt buộc, ISO 8601 |

**Response 200 — thành công:**

```json
{
  "access_granted": true,
  "reason": "Valid student card",
  "person_id": "SV001",
  "person_name": "Nguyen Van A",
  "gate_id": "gate-main",
  "direction": "IN",
  "event_id": "acc-20260502-0001",
  "checked_at": "2026-05-02T07:30:01Z"
}
```

**Response 200 — từ chối (vẫn 200, business logic reject):**

```json
{
  "access_granted": false,
  "reason": "Card expired",
  "person_id": null,
  "gate_id": "gate-main",
  "direction": "IN",
  "event_id": "acc-20260502-0002",
  "checked_at": "2026-05-02T07:30:01Z"
}
```

**Response lỗi chuẩn (400, 404, 500):**

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "direction must be IN or OUT",
    "details": []
  }
}
```

### 4.3 Event gửi sang Core Business (B6)

Sau khi xử lý xong, Access Gate gọi HTTP tới Core (async hoặc sync — khuyến nghị **sync đơn giản** cho MVP):

```http
POST http://core-business:8000/api/v1/events/access
Content-Type: application/json
```

```json
{
  "event_id": "acc-20260502-0001",
  "card_id": "RFID-2026-001",
  "person_id": "SV001",
  "gate_id": "gate-main",
  "direction": "IN",
  "access_granted": true,
  "reason": "Valid student card",
  "timestamp": "2026-05-02T07:30:00",
  "source_service": "access-gate-b3"
}
```

> **Lưu ý:** URL và schema này phải **thống nhất với nhóm B6** trong buổi học tích hợp. Nếu B6 chưa sẵn sàng, vẫn implement client + mock server để test.

### 4.4 Event gửi sang Analytics (B5)

```http
POST http://analytics:8000/api/v1/ingest/access
Content-Type: application/json
```

```json
{
  "event_id": "acc-20260502-0001",
  "gate_id": "gate-main",
  "direction": "IN",
  "access_granted": true,
  "person_type": "student",
  "timestamp": "2026-05-02T07:30:00"
}
```

### 4.5 OpenAPI — khung khởi tạo

Tạo file `openapi.yaml` ở root repo. Cấu trúc tối thiểu:

```yaml
openapi: 3.0.3
info:
  title: Access Gate Service - Product B
  version: 1.0.0
  description: Service kiểm soát ra/vào campus (Nhóm B3)

servers:
  - url: http://localhost:3003
    description: Local development

paths:
  /health:
    get:
      summary: Health check
      responses:
        "200":
          description: Service is healthy

  /api/v1/access/check:
    post:
      summary: Kiểm tra quyền ra/vào
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/AccessCheckRequest"
      responses:
        "200":
          description: Kết quả kiểm tra
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/AccessCheckResponse"
        "400":
          description: Dữ liệu không hợp lệ

components:
  schemas:
    AccessCheckRequest:
      type: object
      required: [card_id, gate_id, direction, timestamp]
      properties:
        card_id:
          type: string
          example: RFID-2026-001
        gate_id:
          type: string
          example: gate-main
        direction:
          type: string
          enum: [IN, OUT]
        timestamp:
          type: string
          format: date-time

    AccessCheckResponse:
      type: object
      properties:
        access_granted:
          type: boolean
        reason:
          type: string
        person_id:
          type: string
          nullable: true
        event_id:
          type: string
        checked_at:
          type: string
          format: date-time
```

Mở rộng dần các endpoint còn lại và `ErrorResponse`.

---

## 5. Kiến trúc và công nghệ đề xuất

Nhóm **tự chọn stack**, miễn đáp ứng hợp đồng API. Gợi ý 2 phương án phổ biến:

### Phương án A — Node.js + Fastify (khuyến nghị cho nhóm thích JS)

| Thành phần | Công nghệ |
|------------|-----------|
| API | Fastify hoặc Express |
| Validation | Zod hoặc Joi |
| Database | SQLite (dev) / PostgreSQL (prod demo) |
| HTTP client | `fetch` hoặc `axios` gọi B5, B6 |
| Test | Newman + Postman |
| Container | Docker |

### Phương án B — Python + FastAPI

| Thành phần | Công nghệ |
|------------|-----------|
| API | FastAPI |
| Validation | Pydantic |
| Database | SQLAlchemy + SQLite/PostgreSQL |
| HTTP client | `httpx` |
| Test | Newman + Postman |
| Container | Docker |

### Luồng xử lý nội bộ (logic chính)

```text
POST /api/v1/access/check
    │
    ├─► Validate input
    │
    ├─► Tra cứu card trong DB
    │       ├─ Không tìm thấy → access_granted=false, reason="Unknown card"
    │       ├─ Hết hạn / khóa → access_granted=false
    │       └─ Hợp lệ → access_granted=true
    │
    ├─► Ghi access_log vào DB
    │
    ├─► Gọi Core Business (B6) — log lỗi nếu fail, không crash request chính
    │
    ├─► Gọi Analytics (B5) — tương tự
    │
    └─► Trả response cho client
```

**Quy tắc thiết kế quan trọng:** Response cho client phải trả về **ngay cả khi B5/B6 tạm thời không phản hồi**. Ghi log lỗi integration để demo minh chứng.

---

## 6. Cấu trúc thư mục dự án

```text
B3_Access Gate/
├── src/                          # Source code service
│   ├── app.js / main.py          # Entry point
│   ├── routes/                   # Route handlers
│   ├── services/                 # Business logic
│   ├── integrations/             # Client gọi B5, B6
│   ├── models/                   # DB models
│   └── utils/                    # Helper, validation
├── db/
│   └── seed.sql                  # Dữ liệu mẫu thẻ RFID
├── frontend/                     # (Optional) UI demo quẹt thẻ
├── evidence/
│   ├── access_gate_test_report.md
│   ├── screenshots/
│   └── logs/
├── postman/
│   └── access_gate.postman_collection.json
├── openapi.yaml
├── service_boundary.md
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── RUN_LOCAL.md
├── package.json / requirements.txt
└── HUONG_DAN_TRIEN_KHAI.md       # File này
```

---

## 7. Triển khai từng bước

### Bước 1 — Khởi tạo project và health check

1. Tạo repo Git (GitHub/GitLab).
2. Khởi tạo project Node hoặc Python.
3. Implement `GET /health` trả `{ "status": "ok", "service": "access-gate-b3" }`.
4. Chạy local, chụp screenshot Postman → bắt đầu folder `evidence/`.

### Bước 2 — Database và seed dữ liệu

Tạo bảng tối thiểu:

**`cards`**

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| card_id | string PK | RFID-2026-001 |
| person_id | string | SV001, NV010 |
| person_name | string | Họ tên |
| person_type | enum | student, staff, guest |
| status | enum | active, expired, blocked |
| expired_at | datetime | nullable |

**`access_logs`**

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| event_id | string PK | acc-20260502-0001 |
| card_id | string | |
| person_id | string | nullable |
| gate_id | string | |
| direction | string | IN/OUT |
| access_granted | boolean | |
| reason | string | |
| timestamp | datetime | |
| created_at | datetime | |

Seed ít nhất **5 thẻ** với các trường hợp: hợp lệ, hết hạn, bị khóa, không tồn tại (test qua Postman).

### Bước 3 — Implement `POST /api/v1/access/check`

Pseudo-code:

```javascript
async function checkAccess(body) {
  validate(body);

  const card = await db.findCard(body.card_id);
  let accessGranted = false;
  let reason = "Unknown card";
  let personId = null;

  if (card) {
    if (card.status === "active") {
      accessGranted = true;
      reason = card.person_type === "student"
        ? "Valid student card"
        : "Valid staff card";
      personId = card.person_id;
    } else if (card.status === "expired") {
      reason = "Card expired";
    } else if (card.status === "blocked") {
      reason = "Card blocked";
    }
  }

  const event = await db.saveAccessLog({ ...body, accessGranted, reason, personId });

  // Integration — không block response chính
  notifyCoreBusiness(event).catch(err => logger.error(err));
  notifyAnalytics(event).catch(err => logger.error(err));

  return buildResponse(event);
}
```

### Bước 4 — Implement `GET /api/v1/access/logs`

- Query params: `gate_id`, `direction`, `from`, `to`, `page`, `limit`.
- Dùng cho demo và Analytics đối chiếu dữ liệu.

### Bước 5 — Integration clients (B5, B6)

Tạo module `integrations/coreBusinessClient.js`:

```javascript
async function sendAccessEvent(event) {
  const url = process.env.CORE_BUSINESS_URL;
  if (!url) {
    logger.warn("CORE_BUSINESS_URL not set, skip integration");
    return;
  }

  const response = await fetch(`${url}/api/v1/events/access`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(mapToCorePayload(event)),
    signal: AbortSignal.timeout(3000)
  });

  if (!response.ok) {
    throw new Error(`Core Business error: ${response.status}`);
  }
}
```

Làm tương tự cho Analytics.

### Bước 6 — Front-end demo (optional)

Trang HTML/React đơn giản:

- Dropdown chọn `gate_id`, `direction`.
- Input `card_id` hoặc nút mô phỏng quẹt thẻ mẫu.
- Hiển thị kết quả `access_granted` + `reason`.
- **Không thay thế** Postman test.

### Bước 7 — Logging

Ghi log có cấu trúc (JSON hoặc text):

```text
[2026-05-02T07:30:01Z] ACCESS_CHECK card_id=RFID-2026-001 granted=true event_id=acc-20260502-0001
[2026-05-02T07:30:01Z] INTEGRATION core_business=success event_id=acc-20260502-0001
[2026-05-02T07:30:02Z] INTEGRATION analytics=failed reason=timeout
```

Log là **minh chứng nghiệm thu** — lưu vào `evidence/logs/`.

---

## 8. Kết nối với service khác (Product B)

### 8.1 Bảng service Product B

| Nhóm | Service | Port gợi ý (local) | Liên quan B3 |
|------|---------|-------------------|--------------|
| B1 | IoT Ingestion | 3001 | Không bắt buộc trực tiếp |
| B2 | Camera Stream | 3002 | Không bắt buộc trực tiếp |
| **B3** | **Access Gate** | **3003** | **Service của bạn** |
| B4 | AI Vision | 3004 | Không bắt buộc trực tiếp |
| B5 | Analytics | 3005 | **B3 gửi dữ liệu tới** |
| B6 | Core Business | 3006 | **B3 gửi event tới** |
| B7 | Notification | 3007 | Gián tiếp qua B6 |

### 8.2 Chiến lược tích hợp khi nhóm khác chưa xong

1. **Mock server:** Dùng Postman Mock hoặc `json-server` / `wiremock` mô phỏng B5, B6.
2. **Contract-first:** Thống nhất `openapi.yaml` trước, implement song song.
3. **Docker network:** Khi tích hợp thật, các service cùng network `product-b-net`.

Ví dụ `.env` khi tích hợp:

```env
PORT=3003
DATABASE_URL=postgresql://access:access@db:5432/access_gate
CORE_BUSINESS_URL=http://core-business:3006
ANALYTICS_URL=http://analytics:3005
LOG_LEVEL=info
```

### 8.3 Kịch bản demo tích hợp (nghiệm thu)

| # | Kịch bản | Kỳ vọng |
|---|----------|---------|
| 1 | Quẹt thẻ sinh viên hợp lệ, IN | `access_granted=true`, log lưu DB, B6 và B5 nhận event |
| 2 | Quẹt thẻ hết hạn | `access_granted=false`, reason rõ ràng |
| 3 | Quẹt thẻ không tồn tại | `access_granted=false`, reason="Unknown card" |
| 4 | Quẹt OUT sau IN | Log đủ cặp IN/OUT, Analytics đếm đúng |
| 5 | B6 tạm tắt | Access Gate vẫn trả response, log ghi integration failed |
| 6 | Gửi `direction=INVALID` | HTTP 400, error model chuẩn |

---

## 9. Docker và Docker Compose

### 9.1 Dockerfile (ví dụ Node.js)

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3003

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:3003/health || exit 1

CMD ["node", "src/app.js"]
```

### 9.2 docker-compose.yml (service + PostgreSQL)

```yaml
services:
  access-gate:
    build: .
    ports:
      - "3003:3003"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    networks:
      - product-b-net

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: access
      POSTGRES_PASSWORD: access
      POSTGRES_DB: access_gate
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U access -d access_gate"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - product-b-net

volumes:
  pgdata:

networks:
  product-b-net:
    external: true   # tạo trước: docker network create product-b-net
```

### 9.3 Lệnh triển khai

```bash
# Tạo network dùng chung Product B (chạy 1 lần)
docker network create product-b-net

# Build và chạy Access Gate
docker compose up --build -d

# Kiểm tra
curl http://localhost:3003/health
```

### 9.4 File `.env.example`

```env
PORT=3003
NODE_ENV=development
DATABASE_URL=postgresql://access:access@localhost:5432/access_gate

# URL service Product B — cập nhật khi tích hợp
CORE_BUSINESS_URL=http://localhost:3006
ANALYTICS_URL=http://localhost:3005

# Timeout integration (ms)
INTEGRATION_TIMEOUT_MS=3000
LOG_LEVEL=info
```

### 9.5 File `RUN_LOCAL.md`

Ghi rõ:

1. Yêu cầu: Docker, Node 20 / Python 3.11, Postman.
2. Cách copy `.env.example` → `.env`.
3. Lệnh chạy local không Docker.
4. Lệnh `docker compose up`.
5. Lệnh chạy Newman test.
6. URL health check và Swagger UI (nếu có).

---

## 10. Kiểm thử Postman / Newman

### 10.1 Collection tối thiểu

Tạo `postman/access_gate.postman_collection.json` với các request:

| Tên test | Method | Assert |
|----------|--------|--------|
| Health Check | GET /health | status 200, body có `status` |
| Access Valid Student IN | POST /access/check | `access_granted === true` |
| Access Expired Card | POST /access/check | `access_granted === false` |
| Access Unknown Card | POST /access/check | `access_granted === false` |
| Access Invalid Direction | POST /access/check | status 400 |
| Get Access Logs | GET /access/logs | status 200, array |

### 10.2 Environment Postman

```json
{
  "base_url": "http://localhost:3003",
  "valid_card_id": "RFID-2026-001",
  "expired_card_id": "RFID-2026-999"
}
```

### 10.3 Chạy Newman (CLI)

```bash
npm install -g newman

newman run postman/access_gate.postman_collection.json \
  -e postman/local.postman_environment.json \
  --reporters cli,json \
  --reporter-json-export evidence/newman_report.json
```

### 10.4 Test report

Ghi vào `evidence/access_gate_test_report.md`:

- Ngày chạy test
- Môi trường (local / Docker)
- Số test pass/fail
- Screenshot Postman
- Link hoặc paste kết quả Newman

---

## 11. Artefact bắt buộc phải nộp

Dựa trên yêu cầu chung học phần và artefact mẫu của IoT Ingestion, nhóm B3 nên nộp:

| # | File / Folder | Mô tả |
|---|---------------|-------|
| 1 | `openapi.yaml` | Hợp đồng API đầy đủ |
| 2 | `service_boundary.md` | Ranh giới dịch vụ, actor, provider/consumer |
| 3 | `postman/access_gate.postman_collection.json` | Bộ test tích hợp |
| 4 | `Dockerfile` | Đóng gói service |
| 5 | `docker-compose.yml` | Nếu dùng DB (khuyến nghị có) |
| 6 | `.env.example` | Biến môi trường mẫu, không chứa secret thật |
| 7 | `RUN_LOCAL.md` | Hướng dẫn chạy local/Docker |
| 8 | `evidence/access_gate_test_report.md` | Báo cáo kiểm thử |
| 9 | Source code | `src/` hoặc tương đương |
| 10 | `evidence/screenshots/` | Ảnh chụp API, Docker, tích hợp |
| 11 | Video demo (optional) | 3–5 phút, YouTube/Drive |

---

## 12. Demo Pack và nghiệm thu

Khi trình bày cuối kỳ, chuẩn bị **Demo Pack** gồm:

### 12.1 Phần trình bày (5–7 phút)

1. **Service boundary:** Access Gate nhận gì, trả gì, gọi ai.
2. **OpenAPI:** Show endpoint chính và error model.
3. **Live demo:** Postman quẹt thẻ → kết quả → log DB.
4. **Tích hợp:** Show request sang B6/B5 (Postman Console hoặc log).
5. **Docker:** `docker compose up` → health check OK.
6. **Test report:** Newman pass 100% (hoặc giải thích test fail nếu phụ thuộc nhóm khác).

### 12.2 Câu hỏi giảng viên thường hỏi — gợi ý trả lời

| Câu hỏi | Hướng trả lời |
|---------|---------------|
| Vì sao tách Access Gate khỏi Core Business? | Access Gate xử lý realtime tại cổng; Core xử lý chính sách phức tạp và điều phối cảnh báo. |
| Nếu Core Business down thì sao? | Cổng vẫn trả kết quả local; log integration failed; có thể retry sau. |
| Phân biệt provider/consumer? | B3 là provider cho API check; B3 là consumer khi gọi B5, B6. |
| Status code 200 khi từ chối truy cập? | Đó là kết quả nghiệp vụ hợp lệ, không phải lỗi HTTP — tách business reject vs technical error. |

---

## 13. Checklist trước khi nộp

```text
[ ] openapi.yaml mô tả đủ endpoint, schema, status code
[ ] service_boundary.md rõ ràng provider/consumer
[ ] POST /api/v1/access/check đúng format đề bài
[ ] Có seed data và test case: valid / expired / unknown / invalid input
[ ] Ghi access log vào DB
[ ] Client gọi Core Business (B6) — có log minh chứng
[ ] Client gọi Analytics (B5) — có log minh chứng
[ ] Postman collection chạy pass
[ ] Newman report export vào evidence/
[ ] Dockerfile build thành công
[ ] docker compose up chạy được trên máy sạch (không cài Node/Python)
[ ] RUN_LOCAL.md đủ rõ để người khác chạy được
[ ] .env.example không lộ mật khẩu thật
[ ] Screenshot + test report trong evidence/
[ ] Git repo sạch, README ngắn gọn trỏ tới RUN_LOCAL.md
```

---

## 14. Lộ trình làm việc theo tuần (gợi ý)

| Tuần | Công việc | Deliverable |
|------|-----------|-------------|
| 1 | Phân tích đề, viết `service_boundary.md`, draft `openapi.yaml` | Boundary + OpenAPI v0.1 |
| 2 | Implement health + access/check + DB + seed | API chạy local |
| 3 | Postman tests + Newman + `RUN_LOCAL.md` | Test report v1 |
| 4 | Dockerfile + docker-compose | Chạy bằng Docker |
| 5 | Liên hệ B5, B6 thống nhất contract integration | Integration clients |
| 6 | Tích hợp end-to-end Product B + evidence + demo | Demo Pack hoàn chỉnh |

---

## Phụ lục A — Mẫu nội dung `service_boundary.md`

```markdown
# Service Boundary — Access Gate (B3, Product B)

## Service name
access-gate-b3

## Provider
Nhóm B3 cung cấp API kiểm soát ra/vào cho RFID reader mô phỏng và front-end demo.

## Consumers (gọi Access Gate)
- RFID simulator / Front-end demo
- Postman/Newman (testing)

## Dependencies (Access Gate gọi đi)
- Core Business (B6): POST /api/v1/events/access
- Analytics (B5): POST /api/v1/ingest/access

## Input
AccessCheckRequest: card_id, gate_id, direction, timestamp

## Output
AccessCheckResponse: access_granted, reason, person_id, event_id

## Out of scope
- Gửi notification trực tiếp
- Phân tích AI camera
- Báo cáo tổng hợp campus
```

---

## Phụ lục B — Liên hệ nhóm Product B cần phối hợp sớm

| Nhóm | Nội dung cần thống nhất |
|------|-------------------------|
| **B6 Core Business** | URL, payload, auth (nếu có), response khi nhận access event |
| **B5 Analytics** | Schema metric access, field bắt buộc |
| B7 Notification | Không gọi trực tiếp — xác nhận luồng qua B6 |
| B1, B2, B4 | Không bắt buộc — có thể demo riêng lẻ |

---

## Bước tiếp theo cho nhóm B3

1. Chọn stack (Node/Fastify hoặc Python/FastAPI).
2. Tạo repo và copy cấu trúc thư mục mục 6.
3. Viết `service_boundary.md` và `openapi.yaml` trước khi code nhiều.
4. Liên hệ nhóm **B6** và **B5** trong tuần 1–2 để thống nhất hợp đồng integration.

Nếu cần, có thể yêu cầu scaffold sẵn project (FastAPI/Fastify + Docker + Postman collection mẫu) trực tiếp trong repo này.
