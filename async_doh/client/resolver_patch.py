import asyncio
from functools import partial

from async_dns.core import Address, DNSMessage
from async_dns.resolver import DNSClient

from .client import DoHClient
from .session import set_resolver


async def _request_https(client: DoHClient,
                         req: DNSMessage,
                         addr: Address,
                         timeout=3.0,
                         method='POST'):
    result = await asyncio.wait_for(
        client.request_message(str(addr), req, method), timeout)
    return result


async def patch(method='POST', resolver=None):
    if resolver is not None:
        set_resolver(resolver)
    client = await DoHClient().__aenter__()
    DNSClient.protocols['https'] = partial(_request_https,
                                           client,
                                           method=method)

    async def revoke():
        DNSClient.protocols.pop('https', None)
        await client.__aexit__(None, None, None)

    return revoke


if __name__ == '__main__':
    from async_dns.core import types
    from async_dns.resolver import ProxyResolver

    async def main():
        revoke = await patch()
        resolver = ProxyResolver(proxies=['https://dns.alidns.com/dns-query'])
        res, _ = await resolver.query('www.google.com', types.A)
        print(res)
        await revoke()

    asyncio.run(main())
