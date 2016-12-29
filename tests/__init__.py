import asyncio
import socket

import asynctest

from asyncstream import streams


class BaseTestCase(asynctest.TestCase):
    async def create_socket_server(self, protocol):
        server = await asyncio.get_event_loop().create_server(protocol, '127.0.0.1')
        self.addCleanup(lambda: server.close())
        server_addr = None
        for s in server.sockets:
            if s.family == socket.AF_INET:
                server_addr = s.getsockname()
        return server, server_addr

    async def create_socket_stream(self, addr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setblocking(False)
        await asyncio.get_event_loop().sock_connect(sock, addr)
        stream = streams.SocketStream(sock)
        self.addCleanup(lambda: stream.close)
        return stream
