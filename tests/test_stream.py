import asyncio
import tests

import asyncstream


class TestServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.transport.write(b'hello')

    def connection_lost(self, error):
        self.transport = None

    def data_received(self, data):
        self.transport.write(b'goodbye')
        self.transport.close()


class SocketStreamTestCase(tests.BaseTestCase):
    async def test_read_async(self):

        server, server_addr = await self.create_socket_server(TestServerProtocol)
        stream = await self.create_socket_stream(server_addr)

        self.assertEqual(await stream.read_async(1024), b'hello')
        await stream.write_async(b'hello')
        self.assertEqual(await stream.read_async(1024), b'goodbye')
        self.assertEqual(await stream.read_async(1024), None)

    async def test_read_async_close(self):

        server, server_addr = await self.create_socket_server(TestServerProtocol)
        stream = await self.create_socket_stream(server_addr)

        self.assertEqual(await stream.read_async(1024), b'hello')
        await stream.write_async(b'hello')
        self.assertEqual(await stream.read_async(1024), b'goodbye')
        stream.close()
        try:
            await stream.read_async(1024)
        except asyncstream.StreamClosedError:
            pass
        else:
            self.fail("StreamClosed not raised")
