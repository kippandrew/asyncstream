import socket


def create_socket(addr_family, sock_type, sock_proto, reuse_addr=True, reuse_port=False):
    # create a socket
    sock = socket.socket(addr_family, sock_type, sock_proto)

    # enable SO_REUSEADDR
    if reuse_addr:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

    # enable SO_REUSEPORT
    if reuse_port:
        if not hasattr(socket, 'SO_REUSEPORT'):
            raise ValueError('reuse_port not supported by socket module')
        else:
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                raise ValueError('reuse_port not supported by socket module, '
                                 'SO_REUSEPORT defined but not implemented.')

    # Disable IPv4/IPv6 dual stack support (enabled by default on Linux)
    if addr_family == socket.AF_INET6 and hasattr(socket, 'IPPROTO_IPV6'):
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)

    return sock


def _get_addr_info(host, port, family, type, proto):
    # Try to skip getaddrinfo if "host" is already an IP. Users might have
    # handled name resolution in their own code and pass in resolved IPs.
    if not hasattr(socket, 'inet_pton'):
        return

    if proto not in {0, socket.IPPROTO_TCP, socket.IPPROTO_UDP} or host is None:
        return None

    if type == socket.SOCK_STREAM:
        # Linux only:
        #    getaddrinfo() can raise when socket.type is a bit mask.
        #    So if socket.type is a bit mask of SOCK_STREAM, and say
        #    SOCK_NONBLOCK, we simply return None, which will trigger
        #    a call to getaddrinfo() letting it process this request.
        proto = socket.IPPROTO_TCP
    elif type == socket.SOCK_DGRAM:
        proto = socket.IPPROTO_UDP
    else:
        return None

    if port is None:
        port = 0
    elif isinstance(port, bytes) and port == b'':
        port = 0
    elif isinstance(port, str) and port == '':
        port = 0
    else:
        # If port's a service name like "http", don't skip getaddrinfo.
        try:
            port = int(port)
        except (TypeError, ValueError):
            return None

    if family == socket.AF_UNSPEC:
        afs = [socket.AF_INET]
        if hasattr(socket, 'AF_INET6'):
            afs.append(socket.AF_INET6)
    else:
        afs = [family]

    if isinstance(host, bytes):
        host = host.decode('idna')
    if '%' in host:
        # Linux's inet_pton doesn't accept an IPv6 zone index after host,
        # like '::1%lo0'.
        return None

    for af in afs:
        try:
            socket.inet_pton(af, host)
            # The host has already been resolved.
            return af, type, proto, '', (host, port)
        except OSError:
            pass

    # "host" is not an IP address.
    return None


def resolve(address, *, family=0, type=socket.SOCK_STREAM, proto=0, flags=0, loop=None):
    host, port = address[:2]
    info = _get_addr_info(host, port, family, type, proto)
    if info is not None:
        # "host" is already a resolved IP.
        fut = loop.create_future()
        fut.set_result([info])
        return fut
    else:
        return loop.getaddrinfo(host, port, family=family, type=type, proto=proto, flags=flags)
