import requests
from .response_type import buildSocketMessageFromDict

class DevinAPI:
    @staticmethod
    def build_headers(token):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    @staticmethod
    def fetch_token(user_id):
        headers = DevinAPI.build_headers('.')
        params = {}
        if user_id:
            params['uid'] = user_id
        response = requests.get(f"http://localhost:3001/api/auth", headers=headers, params=params)
        if response.status_code != 200:
            raise Exception("Get token failed.")
        data = response.json()
        return data
    
    @staticmethod
    def fetch_messages(token):
        headers = DevinAPI.build_headers(token)
        response = requests.get(f"http://localhost:3001/api/messages", headers=headers)
        if response.status_code != 200:
            raise Exception("Get messages failed.")
        data = response.json()
        messages = data.get('messages')
        assert messages is not None
        assert isinstance(messages, list)
        def map_to_socket_message(message):
            payload = message.get('payload')
            assert payload is not None
            return buildSocketMessageFromDict(payload)
        payloads = map(map_to_socket_message, messages)
        return list(payloads)