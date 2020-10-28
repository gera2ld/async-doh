import asyncio
import socket
from typing import Any, Dict, List, Optional
from aiohttp import web, TCPConnector, ClientSession
from aiohttp.abc import AbstractResolver
from aiohttp.helpers import get_running_loop
from async_dns import types

_resolver = None

def set_resolver(resolver):
    global _resolver
    _resolver = resolver

class AsyncResolver(AbstractResolver):
    def __init__(self, loop: Optional[asyncio.AbstractEventLoop]=None) -> None:
        self._loop = get_running_loop(loop)

    async def resolve(self, host: str, port: int=0,
                      family: int=socket.AF_INET) -> List[Dict[str, Any]]:
        if family == socket.AF_INET:
            qtype = types.A
        elif family == socket.AF_INET6:
            qtype = types.AAAA
        else:
            qtype = types.ANY
        res = await _resolver.query(host, qtype)
        hosts = []
        if res:
            for item in res.an:
                if item.qtype in (types.A, types.AAAA):
                    hosts.append({
                        'hostname': host,
                        'host': item.data,
                        'port': port,
                        'family': socket.AF_INET if item.qtype == types.A else socket.AF_INET6,
                        'proto': 0,
                        'flags': socket.AI_NUMERICHOST,
                    })
        return hosts

    async def close(self) -> None:
        pass

def create_session():
    if _resolver is None:
        return ClientSession()
    resolver = AsyncResolver()
    connector = TCPConnector(force_close=True, resolver=resolver)
    return ClientSession(connector=connector)
