import requests

def build_headers(token):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

def fetch_token(token, user_id):
    headers = build_headers(token)
    params = {}
    if user_id:
        params['uid'] = user_id
    response = requests.get(f"http://localhost:3001/api/auth", headers=headers, params=params)
    if response.status_code != 200:
        raise Exception("Get token failed.")
    data = response.json()
    return data