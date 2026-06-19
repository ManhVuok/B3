import json

with open('postman/access_gate.postman_collection.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Add X-API-Key header to all requests
for item in data.get('item', []):
    req = item.get('request', {})
    headers = req.get('header', [])
    headers.append({'key': 'X-API-Key', 'value': 'DVKN2026-SECRET-KEY'})
    req['header'] = headers

# Create a new test case for 401 Unauthorized
missing_auth_item = {
    'name': 'Access Check - Missing Auth',
    'request': {
        'method': 'POST',
        'header': [{'key': 'Content-Type', 'value': 'application/json'}],
        'body': {
            'mode': 'raw',
            'raw': '{\\n  \"card_id\": \"{{valid_card_id}}\",\\n  \"gate_id\": \"gate-main\",\\n  \"direction\": \"IN\",\\n  \"timestamp\": \"2026-05-02T07:30:00\"\\n}'
        },
        'url': '{{base_url}}/api/v1/access/check'
    },
    'event': [
        {
            'listen': 'test',
            'script': {
                'exec': [
                    'pm.test(\"Status 401 Unauthorized\", function () { pm.response.to.have.status(401); });'
                ],
                'type': 'text/javascript'
            }
        }
    ]
}

data['item'].append(missing_auth_item)

with open('postman/access_gate.postman_collection.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("Postman collection updated successfully.")
