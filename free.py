#!/usr/bin/env python3

import argparse
import json
import sys

from pprint import pprint as pp
from signal import signal, SIGPIPE, SIG_DFL
from time import sleep
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import quote

VERBOSE = 0

def update(token, ip='', timeout=10.0):
    url = "http://sync.afraid.org/u/"
    url += f"{quote(token, safe='')}/?content-type=json"
    if ip:
        url += f"&myip={quote(ip, safe='')}"
    if VERBOSE > 0:
        print(f"# url: {url}")

    try:
        rsp = urlopen(url=url, timeout=timeout)
    except URLError as e:
        return f"URLError {e} for url='{url}'"

    if rsp.status != 200:
         return f"bad status={rsp.status} for url='{url}'"

    data = json.loads(rsp.read())
    if VERBOSE > 0:
        print("# Response data:")
        pp(data)

    msg = []
    for t in data['targets']:
        if t['statuscode'] not in (0, 100):  # Changed, Same
            msg.append(f"host='{t['host']}' status='{t['statustext']}'")
    return '; '.join(msg)


def main(args_raw):
    p = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='FreeDNS (https://freedns.afraid.org) DDNS IP updater'
        ' using the Sync v2 API'
        ' (https://freedns.afraid.org/dynamic/v2/tips/)')
    p.add_argument(
        '-i', '--ip',
        default='',
        help='optional IP address, the empty string engages'
        ' server-side auto-detection')
    p.add_argument(
        '-t', '--timeout',
        default=10.0, type=float,
        help='HTTP timeout value in seconds')
    p.add_argument(
        '-v', '--verbose',
        default=0, action='count',
        help='verbosity, repeat to increase')
    p.add_argument(
        'token',
        nargs='+',
        help='token(s) linked to DDNS entry to update')
    args = p.parse_args(args_raw)
    if args.timeout < 0.0:
        p.error("invalid timeout value {args.timeout}")
    global VERBOSE
    VERBOSE = args.verbose

    # If 2+ tokens are given we pause for 1 second between updates.
    # We do this to be nice to FreeDNS. :)
    pause = lambda *args: None
    if len(args.token) >= 2:
        pause = sleep

    for t in args.token:
        msg = update(t, args.ip, args.timeout)
        if msg:
            p.error(msg)
        pause(1)


if __name__ == '__main__':
    signal(SIGPIPE, SIG_DFL)  # Avoid exceptions for broken pipes
    main(sys.argv[1:])
