import asyncio
import socket

from asyncstream import stream
from asyncstream import utils


class StreamServer:
    def __init__(self, callback, loop=None):
        self._callback = callback
        self._loop = loop or asyncio.get_event_loop()
        self.sockets = []

    async def listen(self, host, port=None, family=socket.AF_UNSPEC, flags=socket.AI_PASSIVE, backlog=100):
        # resolve host address
        addresses = await utils.resolve((host, port),
                                        family=family,
                                        type=socket.SOCK_STREAM,
                                        flags=flags,
                                        loop=self._loop)

        # create sockets
        for addr_info in addresses:
            addr_family, sock_type, sock_proto, _, sock_addr = addr_info
            sock = utils.create_socket(addr_family, sock_type, sock_proto)
            sock.bind(sock_addr)
            self.sockets.append(sock)

        # start serving
        for s in self.sockets:
            s.listen(backlog)
            s.setblocking(False)
            self._start_serving(s)

    def _start_serving(self, sock, backlog=100):
        self._loop.add_reader(sock.fileno(), self._accept_connection, sock, backlog)

    def _accept_connection(self, sock, backlog=100):
        # There may be multiple connections waiting. Attempt to accept up to backlog.
        for _ in range(backlog):
            try:
                conn, addr = sock.accept()
                conn.setblocking(False)
            except (BlockingIOError, InterruptedError, ConnectionAbortedError):
                # Early exit because the socket accept buffer is empty.
                return None

            # create a stream
            client_stream = self._create_stream(conn)

            # run callback
            self._run_callback(client_stream, addr)

    def _create_stream(self, sock):
        return stream.SocketStream(sock, self._loop)

    def _run_callback(self, *args, **kwargs):
        if self._callback is not None:
            res = self._callback(*args, **kwargs)
            if asyncio.coroutines.iscoroutine(res):
                self._loop.create_task(res)

    def close(self):
        for s in self.sockets:
            s.close()
