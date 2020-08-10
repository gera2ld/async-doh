import aiohttp
import base64
from async_dns import DNSMessage, REQUEST, Record, types

async def query(url, name, qtype=types.A, method='GET'):
    req = DNSMessage(qr=REQUEST)
    if isinstance(qtype, str):
        qtype = types.get_code(qtype)
    req.qd = [Record(REQUEST, name, qtype)]
    dns = base64.urlsafe_b64encode(req.pack()).decode().rstrip('=')
    async with aiohttp.ClientSession() as session:
        async with session.get(url,
                params={ 'dns': dns },
                headers={ 'accept': 'application/dns-message' }) as resp:
            data = await resp.read()
            result = DNSMessage.parse(data)
            return result

async def query_json(url, name, qtype=types.A, method='GET'):
    if isinstance(qtype, int):
        qtype = types.get_name(qtype)
    async with aiohttp.ClientSession() as session:
        async with session.get(url,
                params={ 'name': name, 'qtype': qtype },
                headers={ 'accept': 'application/dns-json' }) as resp:
            data = await resp.json(content_type='application/dns-json')
            return data

if __name__ == '__main__':
    async def main():
        result = await query('https://1.1.1.1/dns-query', 'www.google.com', 'A')
        print('query:', result)
        result = await query_json('https://1.1.1.1/dns-query', 'www.google.com', 'A')
        print('query_json:', result)
    import asyncio
    asyncio.run(main())
