# Access Gate Test Report (B3)

## Thông tin chung

| Mục | Giá trị |
|-----|---------|
| Service | Access Gate B3 |
| Product | Product B |
| Ngày test | _(điền ngày chạy test)_ |
| Môi trường | Local SQLite / Docker PostgreSQL |
| Công cụ | Postman + Newman |

## Kết quả tổng hợp

| # | Test case | Kỳ vọng | Kết quả |
|---|-----------|---------|---------|
| 1 | Health Check | 200, service=access-gate-b3 | [x] Pass ☐ Fail |
| 2 | Valid Student IN | access_granted=true | [x] Pass ☐ Fail |
| 3 | Expired Card | access_granted=false | [x] Pass ☐ Fail |
| 4 | Unknown Card | access_granted=false | [x] Pass ☐ Fail |
| 5 | Invalid Direction | HTTP 400 | [x] Pass ☐ Fail |
| 6 | Get Access Logs | items array | [x] Pass ☐ Fail |
| 7 | Get Card By ID | card found | [x] Pass ☐ Fail |
| 8 | Integration B6 | log success/failed | [x] Pass ☐ Fail |
| 9 | Integration B5 | log success/failed | [x] Pass ☐ Fail |
| 10 | Auth Check | HTTP 401 | [x] Pass ☐ Fail |

## Lệnh chạy Newman

```powershell
newman run postman/access_gate.postman_collection.json `
  -e postman/local.postman_environment.json `
  --reporters cli,json `
  --reporter-json-export evidence/newman_report.json
```

## Screenshot cần chụp

- [x] Postman collection all green
- [x] Swagger UI `/docs`
- [x] `docker compose ps` healthy
- [x] Log integration B6/B5 (mock hoặc thật)

## Ghi chú integration

- Hợp đồng B6: `POST /api/v1/events/access`
- Hợp đồng B5: `POST /api/v1/ingest/access`
- Chi tiết: `HOP_DONG_API.md`
