import websocket, threading, time, json
from urllib.parse import urlencode

from .devin_auth import TokenStorage

class DevinSocket:
    def __init__(self, user_id):
        self.user_id = user_id
        self.callbacks = {
            "connect": [],
            "receive": [],
            "disconnect": [],
        }
        self._initializing = False
        self._token = None
        self._socket = None
        self.is_socket_connected = False
        self._token_storage = TokenStorage()

    def _try_initialize(self):
        if self._initializing:
            print("Already initializing...")
            return
        self._initializing = True
        try:
            self._token = self._token_storage.get_token(self.user_id)
            self._initialize(self._token)
            
            print('Connected!')
        except Exception as e:
            print(f"Connection failed for {self.user_id}. Retry... {str(e)}")
            print(e)
            self._try_initialize()
        finally:
            self._initializing = False

    def _initialize(self, token: str):
        params = {
            "token": token,
        }

        if self.user_id:
            params["uid"] = self.user_id

        if self._socket:
            self._socket.close()

        ws_url = f"ws://localhost:3001/ws?{urlencode(params)}"
        self.is_socket_connected = False
        self._socket = websocket.WebSocketApp(
            ws_url, 
            on_open=self._on_open, 
            on_message=self._on_message, 
            on_close=self._on_close, 
            on_error=lambda _, e: print(f"Websocket error: {e}"))
        threading.Thread(target=self._socket.run_forever).start()
        
        while not self.is_socket_connected:
            time.sleep(0.1)
        print("Connected socket")
            
    def _on_open(self, ws):
        print("Socket connected")
        self.is_socket_connected = True
        for callback in self.callbacks["connect"]:
            callback(self)
            
    def _on_message(self, ws, message):
        for callback in self.callbacks["receive"]:
            callback(self, message)
            
    def _on_close(self, ws, status, message):
        print("Socket closed", status, message)
        self.is_socket_connected = False
        for callback in self.callbacks["disconnect"]:
            callback(self)

    def register_callback(self, event, callback):
        self.callbacks[event].append(callback)

    def unregister_all_callbacks(self):
        print('Unregistering all callbacks...')
        self.callbacks = {
            "connect": [],
            "receive": [],
            "disconnect": [],
        }

    def is_connected(self):
        return self._socket is not None and self.is_socket_connected

    def send(self, message):
        if self._socket is None:
            self._try_initialize()
        
        if self.is_connected() and self._socket is not None:
            self._socket.send(json.dumps(message))