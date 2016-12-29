_DEFAULT_BUFFER_SIZE = 65536
_DEFAULT_READ_SIZE = 16384

from . import stream
from .error import BufferOverrunError


class StreamReader:
    def __init__(self, stream: stream.BaseStream, buffer_size=_DEFAULT_BUFFER_SIZE, read_size=_DEFAULT_READ_SIZE):
        """
        Create a new instance of the StreamReader class
        """
        self._stream = stream
        self._read_buffer_size = buffer_size
        self._read_buffer = bytearray()
        self._read_size = read_size
        self._eof = False

    async def _read_to_buffer(self):
        data = await self._stream.read_async(self._read_size)
        if data is None:
            self._eof = True
            return
        self._read_buffer.extend(data)
        if len(self._read_buffer) > self._read_buffer_size:
            raise BufferOverrunError()
        return len(data)

    async def read(self, n):
        """
        Read at most n bytes and return at least one byte.
        """

        if n == 0:
            return b''
        else:
            # read data to buffer
            if len(self._read_buffer) < n:
                await self._read_to_buffer()

            # read data from buffer
            data = bytes(self._read_buffer[:n])
            del self._read_buffer[:n]
            return data

    async def read_until_eof(self):
        """
        Read until EOF and return all read bytes.
        """
        chunks = []
        while True:
            chunk = await self.read(self._read_size)
            if not chunk:
                break
            chunks.append(chunk)
        return b''.join(chunks)

    async def read_until(self, separator=b'\n'):
        """
        Read until separator is found.
        """
        sep_len = len(separator)
        if sep_len == 0:
            raise ValueError('Separator should be at least one-byte')

        # offset is the number of bytes from the beginning of the buffer where there is no occurrence of separator.
        offset = 0

        # loop until we find separator in the buffer, exceed the buffer size, or an EOF has happened.
        while True:
            buf_len = len(self._read_buffer)

            # Check if we now have enough data in the buffer for separator to exist
            if buf_len - offset >= sep_len:

                # search for separator in the buffer
                sep_pos = self._read_buffer.find(separator, offset)

                if sep_pos != -1:
                    # separator was found is in the buffer
                    break

                # separator was not found yet
                offset = buf_len + 1 - sep_len

            # check for EOF
            if self._eof:
                # return an empty string
                return b''

            # read more data
            await self._read_to_buffer()

        data = bytes(self._read_buffer[:sep_pos + sep_len])
        del self._read_buffer[:sep_pos + sep_len]
        return bytes(data)

    async def read_line(self):
        pass
