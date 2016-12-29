import asyncio

from .error import StreamClosedError


class BaseStream:
    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._read_future = None
        self._write_buffer = bytearray()
        self._write_future = None
        self._connected = True
        self._closing = False
        self._close_eof = True

    def _create_read_future(self):
        assert self._read_future is None, "Already reading"
        self._read_future = self._loop.create_future()
        return self._read_future

    def _resolve_read(self, result):
        assert self._read_future is not None, "Not reading"
        future = self._read_future
        future.set_result(result)
        self._read_future = None

    def _resolve_read_error(self, error=None):
        assert self._read_future is not None, "Not reading"
        future = self._read_future
        future.set_exception(error)
        self._read_future = None

    def read_async(self, n):
        """
        Read data asynchronously
        :param n:
        :return:
        """
        fd = self.fileno()
        if fd < 0:
            raise StreamClosedError()
        future = self._create_read_future()
        self._loop.add_reader(fd, self._read_ready, fd, n)
        return future

    def _read_ready(self, fd, n):
        """
        The _read_ready callback is invoked when the stream is ready to read
        :param fd:
        :param n:
        :return: None
        """

        if self._read_future.cancelled():
            return

        try:
            data = self._read_fd(fd, n)
        except (BlockingIOError, InterruptedError):
            # if reading would block, keep reading
            pass
        except Exception as ex:
            # error reading
            self._resolve_read_error(ex)
            self._loop.remove_reader(fd)
        else:
            if data:
                # done reading
                self._resolve_read(data)
            else:
                # done reading (EOF received)
                self._resolve_read(None)
                if self._close_eof:
                    self.close()

            # done reading, remove reader
            self._loop.remove_reader(fd)

    def _read_fd(self, fd, n):
        raise NotImplementedError

    def _create_write_future(self):
        assert self._write_future is None, "Already writing"
        self._write_future = self._loop.create_future()
        return self._write_future

    def _resolve_write(self, result):
        assert self._write_future is not None, "Not writing"
        future = self._write_future
        future.set_result(result)
        self._write_future = None

    def _resolve_write_error(self, error=None):
        assert self._write_future is not None, "Not writing"
        future = self._write_future
        future.set_exception(error)
        self._write_future = None

    def write_async(self, data):
        """
        Write data asynchronously
        :param data:
        :return:
        """
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError('data argument must be a bytes-like object, '
                            'not %r' % type(data).__name__)

        fd = self.fileno()
        if fd < 0:
            raise StreamClosedError()

        future = self._create_write_future()
        if not data:
            self._resolve_write(None)
            return future

        # Optimization: attempt to send data immediately
        try:
            n = self._write_fd(fd, data)
        except (BlockingIOError, InterruptedError):
            # if writing would block, keep writing
            pass
        except Exception as ex:
            self._resolve_write_error(ex)
            return future
        else:
            # get data remaining to be written
            data = data[n:]

            # if done writing, resolve future
            if not data:
                self._resolve_write(None)
                return future

        # Not all was written, register write handler to send data asynchronously
        self._write_buffer.extend(data)
        self._loop.add_writer(fd, self._write_ready)
        return future

    def _write_ready(self, fd):
        assert self._write_buffer is not None, "Buffer should not be empty"

        if self._write_future.cancelled():
            return

        try:
            n = self._write_fd(fd, self._write_buffer)
        except (BlockingIOError, InterruptedError):
            # if writing would block, keep writing
            pass
        except Exception as ex:
            # error writing
            self._resolve_write_error(ex)
            self._loop.remove_writer(fd)

            # clear the write buffer
            self._write_buffer.clear()
        else:

            # remove bytes written from the write buffer
            if n:
                del self._write_buffer[:n]

            # check if write buffer is emtpy
            if not self._write_buffer:

                # done writing
                self._resolve_write(None)
                self._loop.remove_writer(fd)

                # if we're closing, now that the buffer is empty go ahead and close
                if self._closing:
                    self._close_fd(fd)

    def _write_fd(self, fd, data):
        raise NotImplementedError

    def close(self):
        if self._closing:
            return
        self._closing = True

        # allow pending writes to finish if the write buffer is not empty
        if not self._write_buffer:
            self._close_fd(self.fileno())

    def _close_fd(self, fd):
        raise NotImplementedError

    def fileno(self):
        raise NotImplementedError()


class SocketStream(BaseStream):
    def __init__(self, socket, loop=None):
        """
        Create new instance of the SocketStream class
        """
        super().__init__(loop)
        self._socket = socket

    def fileno(self):
        if self._socket is not None:
            return self._socket.fileno()
        return -1

    def _close_fd(self, fd):
        self._socket.close()
        self._socket = None

    def _read_fd(self, fd, n):
        return self._socket.recv(n)

    def _write_fd(self, fd, data):
        return self._socket.send(data)
