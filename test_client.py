import requests
import json

# Register a new user
register_data = {
    "email": "test@example.com",
    "password": "password123"
}

response = requests.post('http://localhost:5000/api/register', json=register_data)
print("Register Response:", response.json())

# Login with the new user
login_data = {
    "email": "test@example.com",
    "password": "password123"
}

response = requests.post('http://localhost:5000/api/login', json=login_data)
print("Login Response:", response.json())

# Get the access token for future requests
access_token = response.json().get('access_token')

# Upload a test document
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'multipart/form-data'
}

files = {
    'file': ('test.txt', open('test.txt', 'rb'))
}

data = {
    'title': 'Test Document'
}

response = requests.post('http://localhost:5000/api/upload', headers=headers, files=files, data=data)
print("Upload Response:", response.json())
