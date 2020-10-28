import aiohttp
import asyncio
import base64
from async_dns import DNSMessage, REQUEST, Record, types
from .session import create_session

class DoHClient:
    session = None
    _session_task = None

    async def __aenter__(self):
        if self._session_task is None:
            self._session_task = asyncio.create_task(create_session().__aenter__())
            self.session = await self._session_task
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._session_task is not None:
            session = self.session
            self.session = None
            self._session_task = None
            await session.__aexit__(None, None, None)

    async def request_message(self, url, req, method='GET'):
        headers = {
            'accept': 'application/dns-message',
            'content-type': 'application/dns-message',
        }
        message = req.pack()
        if method == 'GET':
            dns = base64.urlsafe_b64encode(message).decode().rstrip('=')
            params = { 'dns': dns }
            data = None
        else:
            assert method == 'POST', f'Unsupported method: {method}'
            params = None
            data = message
        async with self.session.request(method, url, params=params, data=data, headers=headers) as resp:
            assert 200 <= resp.status < 300, f'Request error: {resp.status}'
            data = await resp.read()
            result = DNSMessage.parse(data)
            return result

    async def query(self, url, name, qtype=types.A, method='GET'):
        req = DNSMessage(qr=REQUEST)
        if isinstance(qtype, str):
            qtype = types.get_code(qtype)
        req.qd = [Record(REQUEST, name, qtype)]
        return await self.request_message(url, req, method)

    async def query_json(self, url, name, qtype=types.A):
        '''Query via JSON APIs for DNS over HTTPS.

        All API calls are HTTP GET requests.
        Reference: https://developers.google.com/speed/public-dns/docs/doh/json
        '''
        if isinstance(qtype, int):
            qtype = types.get_name(qtype)
        async with self.session.get(url,
                params={ 'name': name, 'qtype': qtype },
                headers={ 'accept': 'application/dns-json' }) as resp:
            assert 200 <= resp.status < 300, f'Request error: {resp.status}'
            data = await resp.json(content_type=None)
            return data

if __name__ == '__main__':
    async def main():
        async with DoHClient() as client:
            result = await client.query('http://localhost:8080/dns-query', 'www.google.com', 'A')
            print('query:', result)
            result = await client.query_json('http://localhost:8080/dns-query', 'www.google.com', 'A')
            print('query_json:', result)
    asyncio.run(main())
