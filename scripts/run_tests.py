"""Script chạy tất cả test cases và in kết quả — dùng để tạo evidence."""

import json
import sys
from datetime import datetime, timezone

import httpx

BASE = "http://localhost:3003"
PASS = "[PASS]"
FAIL = "[FAIL]"

results = []


def test(name, status_code, body, checks):
    passed = all(check(status_code, body) for check in checks)
    results.append({"name": name, "status_code": status_code, "body": body, "passed": passed})
    icon = PASS if passed else FAIL
    print(f"{icon} [{status_code}] {name}")
    if not passed:
        print(f"     Response: {json.dumps(body, ensure_ascii=False, default=str)[:200]}")
    return passed


print("=" * 60)
print("Access Gate Service — Test Suite")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Base URL:  {BASE}")
print("=" * 60)
print()

try:
    # 1. Health check
    r = httpx.get(f"{BASE}/health", timeout=5)
    test("Health Check", r.status_code, r.json(),
         [lambda s, b: s == 200, lambda s, b: b.get("service") == "access-gate-b3"])

    # 2. Valid student IN
    r = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-2026-001", "gate_id": "gate-main",
        "direction": "IN", "timestamp": "2026-05-02T07:30:00"
    })
    test("Access Check - Valid Student IN", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("access_granted") is True,
          lambda s, b: b.get("person_id") == "SV001"])

    # 3. Valid student OUT
    r = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-2026-001", "gate_id": "gate-main",
        "direction": "OUT", "timestamp": "2026-05-02T17:30:00"
    })
    test("Access Check - Valid Student OUT", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("access_granted") is True])

    # 4. Staff card
    r = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-2026-010", "gate_id": "gate-lab",
        "direction": "IN", "timestamp": "2026-05-02T08:00:00"
    })
    test("Access Check - Staff Card IN", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("access_granted") is True,
          lambda s, b: "staff" in b.get("reason", "")])

    # 5. Expired card
    r = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-2026-999", "gate_id": "gate-main",
        "direction": "IN", "timestamp": "2026-05-02T07:30:00"
    })
    test("Access Check - Expired Card", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("access_granted") is False,
          lambda s, b: "expired" in b.get("reason", "").lower()])

    # 6. Blocked card
    r = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-2026-888", "gate_id": "gate-lab",
        "direction": "IN", "timestamp": "2026-05-02T08:00:00"
    })
    test("Access Check - Blocked Card", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("access_granted") is False,
          lambda s, b: "blocked" in b.get("reason", "").lower()])

    # 7. Unknown card
    r = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-UNKNOWN-9999", "gate_id": "gate-main",
        "direction": "IN", "timestamp": "2026-05-02T07:30:00"
    })
    test("Access Check - Unknown Card", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("access_granted") is False,
          lambda s, b: "unknown" in b.get("reason", "").lower()])

    # 8. Invalid direction -> 400
    r = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-2026-001", "gate_id": "gate-main",
        "direction": "INVALID", "timestamp": "2026-05-02T07:30:00"
    })
    test("Access Check - Invalid Direction (400)", r.status_code, r.json(),
         [lambda s, b: s == 400,
          lambda s, b: "error" in b])

    # 9. Missing field -> 422/400
    r = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-2026-001"
    })
    test("Access Check - Missing Fields (400)", r.status_code, r.json(),
         [lambda s, b: s in (400, 422)])

    # 10. Get access logs
    r = httpx.get(f"{BASE}/api/v1/access/logs?page=1&limit=10", timeout=5)
    body = r.json()
    test("Get Access Logs", r.status_code, body,
         [lambda s, b: s == 200,
          lambda s, b: isinstance(b.get("items"), list),
          lambda s, b: b.get("total", 0) > 0])

    # 11. Get card by ID
    r = httpx.get(f"{BASE}/api/v1/cards/RFID-2026-001", timeout=5)
    test("Get Card By ID (found)", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("card_id") == "RFID-2026-001"])

    # 12. Get card not found
    r = httpx.get(f"{BASE}/api/v1/cards/RFID-NOT-EXIST", timeout=5)
    test("Get Card By ID (not found - 404)", r.status_code, r.json(),
         [lambda s, b: s == 404])

    # 13. Integration B5 health
    r = httpx.get("http://localhost:3005/health", timeout=5)
    test("Mock B5 Analytics - health", r.status_code, r.json(),
         [lambda s, b: s == 200])

    # 14. Integration B6 health
    r = httpx.get("http://localhost:3006/health", timeout=5)
    test("Mock B6 Core Business - health", r.status_code, r.json(),
         [lambda s, b: s == 200])
         
    # 15. Debounce test
    r1 = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-DEBOUNCE-TEST", "gate_id": "gate-main",
        "direction": "IN", "timestamp": "2026-05-02T07:30:00"
    })
    r2 = httpx.post(f"{BASE}/api/v1/access/check", timeout=8, json={
        "card_id": "RFID-DEBOUNCE-TEST", "gate_id": "gate-main",
        "direction": "IN", "timestamp": "2026-05-02T07:30:01"
    })
    test("Debounce (Hardware Lockout)", r2.status_code, r2.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("access_granted") is False,
          lambda s, b: "debounce" in b.get("reason", "").lower()])

    # 16. Physical Cancel
    event_id = r1.json().get("event_id")
    r = httpx.post(f"{BASE}/api/v1/access/cancel", timeout=8, json={
        "event_id": event_id, "reason": "PHYSICAL_TIMEOUT_NO_PASSAGE"
    })
    test("Physical Passage Cancel", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: b.get("status") == "CANCELLED"])

    # 17. Cursor Pagination
    r = httpx.get(f"{BASE}/api/v1/access/logs/recent?limit=2", timeout=5)
    test("Cursor Pagination (Recent Logs)", r.status_code, r.json(),
         [lambda s, b: s == 200,
          lambda s, b: "next_cursor" in b])

except Exception as e:
    print(f"\n[ERROR]: {e}")
    sys.exit(1)

print()
print("=" * 60)
total = len(results)
passed = sum(1 for r in results if r["passed"])
failed = total - passed
print(f"Result: {passed}/{total} tests PASS  |  {failed} FAIL")
print("=" * 60)

if failed > 0:
    print("\nTest FAIL:")
    for r in results:
        if not r["passed"]:
            print(f"  - {r['name']} (HTTP {r['status_code']})")
