#!/usr/bin/env python3

import argparse
import sys

from pprint import pprint as pp
from signal import signal, SIGPIPE, SIG_DFL
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote

VERBOSE = 0

def update(token, domains, ip='', timeout=10.0):
    a = []
    for d in domains:
        if ',' in d:
            return f"commas not allowed in domain name '{d}'"
        a.append(quote(d, safe=''))
    a = sorted(list(set(a)))  # remove duplicates and sort
    url = 'https://www.duckdns.org/update'
    url += f"?token={quote(token, safe='')}"
    url += f"&domains={','.join(a)}"
    if ip:
        url += f"&ip={quote(ip, safe='')}"
    if VERBOSE > 0:
        url += "&verbose=true"
        print(f"# url: {url}")

    try:
        rsp = urlopen(url=url, timeout=timeout)
    except URLError as e:
        return f"URLError {e} for url='{url}'"

    if rsp.status != 200:
         return f"bad status={rsp.status} for url='{url}'"

    data = rsp.read()
    if len(data) == 0:
        return "no response from server"
    data = data.decode('ascii')
    if VERBOSE > 0:
        print("# Response data:")
        pp(data)
    if not data.startswith('OK'):
        return f"failed token='{token}' domains={domains}"
    return ''


def main(args_raw):
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Duck DNS (https://www.duckdns.org) updater using their'
        ' HTTP API specification (https://www.duckdns.org/spec.jsp)')
    p.add_argument(
        '-i', '--ip',
        default='',
        help='optional IP address, empty string uses'
        ' server-side auto-detection')
    p.add_argument(
        '-t', '--timeout',
        default=60.0, type=float,
        help='HTTP timeout value in seconds')
    p.add_argument(
        '-v', '--verbose',
        default=0, action='count',
        help='verbosity, repeat to increase')
    p.add_argument(
        '-d', '--domain',
        default=[], action='append', required="True",
        help='domain to update, repeat flag for multiple')
    p.add_argument(
        'token',
        help='token linked to DDNS entry to update')
    args = p.parse_args(args_raw)

    if args.timeout < 0.0:
        p.error("invalid timeout value {args.timeout}")
    global VERBOSE
    VERBOSE = args.verbose

    msg = update(args.token, args.domain, args.ip, args.timeout)
    if msg:
        p.error(msg)


if __name__ == '__main__':
    signal(SIGPIPE, SIG_DFL)  # Avoid exceptions for broken pipes
    main(sys.argv[1:])
