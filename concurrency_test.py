import requests
from concurrent.futures import ThreadPoolExecutor

URL = "http://127.0.0.1:8000/orders"

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzkwNDE0Mjg4fQ.qYMOrCtag98cGWaTa_jYrsGF_3R4Ehm6AR0W-b8_ESE"


def place_order(i):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "idempotency-key": f"concurrent-test-{i}"
    }

    body = {
        "items": [
            {
                "product_id": 1,
                "quantity": 1
            }
        ]
    }

    response = requests.post(
        URL,
        headers=headers,
        json=body
    )

    return response.status_code, response.json()


with ThreadPoolExecutor(max_workers=20) as executor:
    results = list(
        executor.map(place_order, range(20))
    )


for i, result in enumerate(results):
    print(i + 1, result)


success = sum(
    1 for status, _ in results
    if status == 200
)

conflicts = sum(
    1 for status, _ in results
    if status == 409
)


print("\nSUCCESS:", success)
print("CONFLICTS:", conflicts)