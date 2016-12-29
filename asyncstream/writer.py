class StreamWriter:
    def __init__(self, stream):
        """
        Create a new instance of the StreamWriter class
        :type stream: BaseStream
        """
        self.stream = stream

    def write(self, data):
        return self.stream.write_async(data)

    def write_line(self, data):
        pass
