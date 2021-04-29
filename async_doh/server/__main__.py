import argparse
import logging
import os

from aiohttp import web
from async_dns.resolver import ProxyResolver

from . import application, set_resolver


def _parse_args():
    parser = argparse.ArgumentParser(prog='python3 -m async_doh.server',
                                     description='DNS over HTTPS wrapper')
    parser.add_argument('-p', '--port', help='port to bind', default=2080)
    parser.add_argument('--host', help='host to bind', default='127.0.0.1')
    parser.add_argument('-n', '--nameservers', nargs='+', help='name servers')
    return parser.parse_args()


def main():
    args = _parse_args()
    if args.nameservers:
        resolver = ProxyResolver(proxies=args.nameservers)
        set_resolver(resolver)
    logging.basicConfig(level=os.environ.get('LOGLEVEL', logging.INFO))
    web.run_app(application, host=args.host, port=args.port)


main()
