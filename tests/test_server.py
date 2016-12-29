import socket

import asyncstream
import asyncstream.factory

import tests


class ServerTestCase(tests.BaseTestCase):
    async def create_server(self, callback):
        server_addr = ('127.0.0.1', None)
        server = asyncstream.factory.StreamServer(callback)
        await server.listen(*server_addr)
        self.addCleanup(lambda: server.close())

        server_addr = None
        for s in server.sockets:
            if s.family == socket.AF_INET:
                server_addr = s.getsockname()

        return server, server_addr

    async def test_server(self):

        async def _handle_connection(stream, addr):
            writer = asyncstream.StreamWriter(stream)
            await writer.write(b'hello world')
            stream.close()

        server, server_addr = await self.create_server(_handle_connection)

        stream = await self.create_socket_stream(server_addr)
        reader = asyncstream.StreamReader(stream)

        data = await reader.read(1024)
        self.assertEqual(data, b'hello world')

