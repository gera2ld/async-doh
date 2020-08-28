# async-doh

[![PyPI](https://img.shields.io/pypi/v/async-doh.svg)]()

DNS over HTTPS based on aiohttp and [async_dns](https://github.com/gera2ld/async_dns).

## Installation

```sh
$ pip install async-doh
```

## Usage

### Client

```py
import asyncio
import aiohttp
from async_doh.client import DoHClient

async def main():
    async with DoHClient() as client:
        result = await client.query('https://1.1.1.1/dns-query', 'www.google.com', 'A')
        print('query:', result)
        result = await client.query_json('https://1.1.1.1/dns-query', 'www.google.com', 'A')
        print('query_json:', result)

asyncio.run(main())
```

### Server

```py
from aiohttp import web
from async_doh.server import application

web.run(application)
```

Now you have `http://localhost:8080/dns-query` as an endpoint.

### Patching async_dns

By importing the patch, async_dns will support queries throught HTTPS (aka DNS over HTTPS):

```py
import asyncio
from async_dns import types
from async_dns.resolver import ProxyResolver
from async_doh.resolver_patch import patch

async def main():
  revoke = await patch()
  resolver = ProxyResolver(proxies=['https://dns.alidns.com/dns-query'])
  print(resolver.query('www.google.com', types.A))
  await revoke()

asyncio.run(main())
```

## References

- <https://tools.ietf.org/html/rfc8484>
