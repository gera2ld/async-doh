import asyncio
from async_dns.resolver import Query
from .client import DoHClient

async def request_https(req, addr, timeout=3.0):
    async with DoHClient() as client:
        result = await client.request_message(str(addr), req)
        return result

Query.protocols['https'] = request_https

if __name__ == '__main__':
    from async_dns import types
    from async_dns.resolver import ProxyResolver
    async def main():
        resolver = ProxyResolver(proxies=['https://dns.alidns.com/dns-query'])
        print('query:', await resolver.query('www.google.com', types.A))
    asyncio.run(main())
