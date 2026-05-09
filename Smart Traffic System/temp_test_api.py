from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)
response = client.get('/')
print('STATUS', response.status_code)
print('TEXT', response.text[:1000])
print('JSON', response.headers.get('content-type'))
