import asyncio

import tests

import asyncstream


class TestServerProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        for i in range(256):
            self.transport.write(b'test')
        self.transport.close()

    def connection_lost(self, error):
        self.transport = None

    def data_received(self, data):
        self.transport.close()


class StreamReaderTestCase(tests.BaseTestCase):
    async def test_read(self):
        server, server_addr = await self.create_socket_server(TestServerProtocol)
        stream = await self.create_socket_stream(server_addr)

        reader = asyncstream.StreamReader(stream)
        self.assertEqual(await reader.read(1024), b'test' * 256)

    async def test_read_until(self):
        server, server_addr = await self.create_socket_server(TestServerProtocol)
        stream = await self.create_socket_stream(server_addr)

        reader = asyncstream.StreamReader(stream)
        self.assertEqual(await reader.read_until(b'test'), b'test')

        stream = await self.create_socket_stream(server_addr)
        reader = asyncstream.StreamReader(stream, buffer_size=512)
        with self.assertRaises(asyncstream.BufferOverrunError):
            await reader.read_until(b'|')

    async def test_read_until_eof(self):
        server, server_addr = await self.create_socket_server(TestServerProtocol)
        stream = await self.create_socket_stream(server_addr)

        reader = asyncstream.StreamReader(stream)
        self.assertEqual(await reader.read_until_eof(), b'test' * 256)

        stream = await self.create_socket_stream(server_addr)
        reader = asyncstream.StreamReader(stream, buffer_size=512)
        with self.assertRaises(asyncstream.BufferOverrunError):
            await reader.read_until_eof()
