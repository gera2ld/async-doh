import asyncio
from functools import partial
from async_dns.resolver import Query
from .client import DoHClient

async def request_https(client, req, addr, timeout=3.0):
    result = await client.request_message(str(addr), req)
    return result

async def patch():
    client = await DoHClient().__aenter__()
    Query.protocols['https'] = partial(request_https, client)
    async def revoke():
        Query.protocols.pop('https', None)
        await client.__aexit__(None, None, None)
    return revoke

if __name__ == '__main__':
    from async_dns import types
    from async_dns.resolver import ProxyResolver
    async def main():
        revoke = await patch()
        resolver = ProxyResolver(proxies=['https://dns.alidns.com/dns-query'])
        print('query:', await resolver.query('www.google.com', types.A))
        await revoke()
    asyncio.run(main())
