import base64
from aiohttp import web
from async_dns import types, DNSMessage, get_nameservers
from async_dns.resolver import ProxyResolver

routes = web.RouteTableDef()
resolver = ProxyResolver(proxies=get_nameservers())

def set_resolver(_resolver):
    global resolver
    resolver = _resolver

@routes.get('/dns-query')
async def doh(request):
    accept = request.headers.get('accept')
    if accept == 'application/dns-json':
        # Ref: https://developers.google.com/speed/public-dns/docs/doh/json
        name = request.query.get('name')
        type = request.query.get('type', 'A')
        cd = request.query.get('cd') in ('1', 'true')
        ct = request.query.get('ct')
        qtype = types.get_code(type)
        assert qtype is not None, web.HTTPBadRequest
        result = await resolver.query(name, qtype)
        assert result is not None, web.HTTPInternalServerError
        data = {
            'Status': result.r,
            'TC': result.tc,
            'RD': result.rd,
            'RA': result.ra,
            'AD': False,
            'CD': cd,
            'Question': [
                { 'name': name, 'type': qtype },
            ],
            'Answer': [
                { 'name': item.name, 'type': item.qtype, 'TTL': item.ttl, 'data': item.data }
                for item in result.an
            ],
        }
        return web.json_response(data, content_type=accept)
    elif accept == 'application/dns-message':
        dns = request.query.get('dns')
        dns = base64.urlsafe_b64decode(dns)
        msg = DNSMessage.parse(dns)
        for question in msg.qd:
            result, _cache = await resolver.query_with_cache(question.name, question.qtype)
            assert result is not None, web.HTTPInternalServerError
            result.qid = msg.qid
            data = result.pack()
            break   # only one question is supported
        return web.Response(body=data)
    else:
        raise web.HTTPBadRequest

application = web.Application()
application.add_routes(routes)

if __name__ == '__main__':
    web.run_app(application)
