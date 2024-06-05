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
        self.__initializing = False
        self.__token = None
        self.__socket = None
        self.__is_socket_connected = False
        self.__token_storage = TokenStorage()

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
        return self.__socket is not None and self.__is_socket_connected

    def send(self, message):
        if self.__socket is None:
            self.__try_initialize()
        
        if self.is_connected() and self.__socket is not None:
            self.__socket.send(json.dumps(message))

    def __try_initialize(self):
        if self.__initializing:
            print("Already initializing...")
            return
        self.__initializing = True
        try:
            self.__token = self.__token_storage.get_token(self.user_id)
            self.__initialize(self.__token)
            
            print('Connected!')
        except Exception as e:
            print(f"Connection failed for {self.user_id}. Retry... {str(e)}")
            print(e)
            self.__try_initialize()
        finally:
            self.__initializing = False

    def __initialize(self, token: str):
        params = {
            "token": token,
        }

        if self.user_id:
            params["uid"] = self.user_id

        if self.__socket:
            self.__socket.close()

        ws_url = f"ws://localhost:3001/ws?{urlencode(params)}"
        self.__is_socket_connected = False
        self.__socket = websocket.WebSocketApp(
            ws_url, 
            on_open=self.__on_open, 
            on_message=self.__on_message, 
            on_close=self.__on_close, 
            on_error=lambda _, e: print(f"Websocket error: {e}"))
        threading.Thread(target=self.__socket.run_forever).start()
        
        start_time = time.time()
        while not self.__is_socket_connected:
            if time.time() - start_time > 60:  # 60 seconds
                raise TimeoutError("Connection attempt timed out after 1 minute")
            time.sleep(0.1)
        print("Connected socket")
            
    def __on_open(self, ws):
        print("Socket connected")
        self.__is_socket_connected = True
        for callback in self.callbacks["connect"]:
            callback(self)
            
    def __on_message(self, ws, message):
        for callback in self.callbacks["receive"]:
            callback(self, message)
            
    def __on_close(self, ws, status, message):
        print("Socket closed", status, message)
        self.__is_socket_connected = False
        for callback in self.callbacks["disconnect"]:
            callback(self)