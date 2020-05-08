"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                usr_log = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == usr_log:
                        self.transport.write(
                            f"Логин {usr_log} занят, попробуйте другой".encode()
                        )
                        self.transport.close()
                        break
                else:
                    self.login = usr_log
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history()
        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()
        self.server.write_history(encoded)

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")

    def send_history(self):
        if len(self.server.history) != 0:
            self.transport.write("История сообщений: ".encode())
        for msg in self.server.history[::-1][:10]:
            self.transport.write(msg + "\n".encode())


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    def write_history(self, msg):
        self.history.append(msg)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
