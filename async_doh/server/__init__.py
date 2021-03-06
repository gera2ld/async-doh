import base64
import logging

from aiohttp import web
from async_dns.core import DNSMessage, get_nameservers, types
from async_dns.resolver import BaseResolver, ProxyResolver

routes = web.RouteTableDef()
resolver = ProxyResolver(proxies=get_nameservers())


def set_resolver(_resolver: BaseResolver):
    global resolver
    resolver = _resolver


async def handle_json_api(request):
    '''JSON API for DNS over HTTPS

    Reference: https://developers.google.com/speed/public-dns/docs/doh/json
    '''
    assert request.method == 'GET', web.HTTPMethodNotAllowed
    accept = request.headers.get('accept')
    assert accept == 'application/dns-json', web.HTTPBadRequest
    name = request.query.get('name')
    type = request.query.get('type', 'A')
    cd = request.query.get('cd') in ('1', 'true')
    # ct = request.query.get('ct')
    qtype = types.get_code(type)
    assert qtype is not None, web.HTTPBadRequest
    result, _ = await resolver.query(name, qtype)
    question = [{'name': name, 'type': qtype}]
    answers = [{
        'name': item.name,
        'type': item.qtype,
        'TTL': item.ttl,
        'data': item.data
    } for item in result.an]
    data = {
        'Status': result.r,
        'TC': result.tc,
        'RD': result.rd,
        'RA': result.ra,
        'AD': False,
        'CD': cd,
        'Question': question,
        'Answer': answers,
    }
    logging.info('[JSON][%s] %s %s %d', request.method, name,
                 types.get_name(qtype), result.r)
    return web.json_response(data, content_type=accept)


async def handle_message_api(request):
    accept = request.headers.get('accept')
    assert accept == 'application/dns-message', web.HTTPBadRequest
    if request.method == 'GET':
        dns = request.query.get('dns')
        dns += '=' * ((4 - len(dns) % 4) % 4)
        dns = base64.urlsafe_b64decode(dns)
    else:
        assert request.method == 'POST', web.HTTPMethodNotAllowed
        assert request.headers.get(
            'content-type') == 'application/dns-message', web.HTTPBadRequest
        dns = await request.read()
    msg = DNSMessage.parse(dns)
    for question in msg.qd:
        result, _ = await resolver.query(question.name, question.qtype)
        result.qid = msg.qid
        data = result.pack()
        logging.info('[MSG][%s] %s %s %d', request.method, question.name,
                     types.get_name(question.qtype), result.r)
        # only one question is supported
        return web.Response(body=data)
    raise web.HTTPInternalServerError


@routes.get('/dns-query')
@routes.post('/dns-query')
async def doh(request):
    accept = request.headers.get('accept')
    if accept == 'application/dns-json':
        return await handle_json_api(request)
    elif accept == 'application/dns-message':
        return await handle_message_api(request)
    else:
        raise web.HTTPBadRequest


application = web.Application()
application.add_routes(routes)
