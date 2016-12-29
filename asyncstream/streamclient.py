import asyncio
import socket

from . import stream

from . import utils


class StreamClient:
    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()

    async def connect(self, host, port, family=socket.AF_UNSPEC, flags=socket.AI_PASSIVE):
        # resolve host address
        addr_info = await utils.resolve((host, port),
                                        family=family,
                                        type=socket.SOCK_STREAM,
                                        flags=flags,
                                        loop=self._loop)

        # create socket
        addr_family, sock_type, sock_proto, _, sock_addr = addr_info[0]
        sock = utils.create_socket(addr_family, sock_type, sock_proto)

        # connect socket
        await self._loop.sock_connect(sock, sock_addr)

        # return stream
        return stream.SocketStream(sock, self._loop)
