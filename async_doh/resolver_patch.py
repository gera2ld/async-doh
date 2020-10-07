import asyncio
from functools import partial
from async_dns.resolver import Query
from .client import DoHClient

async def request_https(client, req, addr, timeout=3.0, method='POST'):
    result = await client.request_message(str(addr), req, method)
    return result

async def patch(method='POST'):
    client = await DoHClient().__aenter__()
    Query.protocols['https'] = partial(request_https, client, method=method)
    async def revoke():
        Query.protocols.pop('https', None)
        await client.__aexit__(None, None, None)
    return revoke
