import jwt, json, os
from .devin_api import DevinAPI

class FilePersistentTokenStorage:
    def __init__(self, filename):
        self.filename = filename
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump({}, f)

    def save_token(self, user_id, token):
        with open(self.filename, 'r+') as f:
            data = json.load(f)
            data[user_id] = token
            f.seek(0)
            json.dump(data, f)
            f.truncate()

    def retrieve_token(self, user_id):
        with open(self.filename, 'r') as f:
            data = json.load(f)
            return data.get(user_id)

class TokenStorage:
    def __init__(self):
        self.__storage = FilePersistentTokenStorage("tokens.json")

    @staticmethod
    def __validate_token(token):
        try:
            claims = jwt.decode(token, options={"verify_signature": False})
            return not (claims.get('sid') is None or claims.get('sid') == '')
        except Exception:
            return False

    def get_token(self, user_id):
        token = self.__storage.retrieve_token(user_id) or ""
        if self.__validate_token(token):
            return token

        data = DevinAPI.fetch_token(user_id)
        if data.get('token') is None or data.get('token') == '':
            raise Exception("Get token failed.")
        new_token = data.get('token')
        if self.__validate_token(new_token):
            self.__storage.save_token(user_id, new_token)
            return new_token
        raise Exception("Token validation failed.")