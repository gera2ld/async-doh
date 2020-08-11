import aiohttp
import asyncio
import base64
from async_dns import DNSMessage, REQUEST, Record, types

class DoHClient:
    session = None
    _session_task = None

    async def __aenter__(self):
        if self._session_task is None:
            self._session_task = asyncio.create_task(aiohttp.ClientSession().__aenter__())
            self.session = await self._session_task
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session_task is not None:
            session = self.session
            self.session = None
            self._session_task = None
            await session.__aexit__(None, None, None)

    async def query(self, url, name, qtype=types.A, method='GET'):
        req = DNSMessage(qr=REQUEST)
        if isinstance(qtype, str):
            qtype = types.get_code(qtype)
        req.qd = [Record(REQUEST, name, qtype)]
        dns = base64.urlsafe_b64encode(req.pack()).decode().rstrip('=')
        async with self.session.get(url,
                params={ 'dns': dns },
                headers={ 'accept': 'application/dns-message' }) as resp:
            data = await resp.read()
            result = DNSMessage.parse(data)
            return result

    async def query_json(self, url, name, qtype=types.A, method='GET'):
        if isinstance(qtype, int):
            qtype = types.get_name(qtype)
        async with self.session.get(url,
                params={ 'name': name, 'qtype': qtype },
                headers={ 'accept': 'application/dns-json' }) as resp:
            data = await resp.json(content_type=None)
            return data

if __name__ == '__main__':
    async def main():
        async with DoHClient() as client:
            result = await client.query('https://doh.pub/dns-query', 'www.google.com', 'A')
            print('query:', result)
            result = await client.query_json('https://doh.pub/dns-query', 'www.google.com', 'A')
            print('query_json:', result)
    asyncio.run(main())
