#!/usr/bin/env python
# flake8: noqa: E402
'''
A WebSocket server that echos back whatever it receives from the client.
Copyright 2010 Joel Martin
Licensed under LGPL version 3 (see docs/LICENSE.LGPL-3)

You can make a cert/key with openssl using:
openssl req -new -x509 -days 365 -nodes -out self.pem -keyout self.pem
as taken from http://docs.python.org/dev/library/ssl.html#certificates
'''

import logging
import optparse
import os
import select
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from websockify.websockifyserver import WebSockifyServer
from websockify.websockifyserver import WebSockifyRequestHandler


class WebSocketEcho(WebSockifyRequestHandler):
    """
    WebSockets server that echos back whatever is received from the
    client.  """
    buffer_size = 8096

    def new_websocket_client(self):
        """
        Echo back whatever is received.
        """

        cqueue = []
        c_pend = 0
        cpartial = ""  # noqa: F841
        rlist = [self.request]

        while True:
            wlist = []

            if cqueue or c_pend:
                wlist.append(self.request)
            ins, outs, excepts = select.select(rlist, wlist, [], 1)
            if excepts:
                raise Exception("Socket exception")

            if self.request in outs:
                # Send queued target data to the client
                c_pend = self.send_frames(cqueue)
                cqueue = []

            if self.request in ins:
                # Receive client data, decode it, and send it back
                frames, closed = self.recv_frames()
                cqueue.extend(frames)

                if closed:
                    break


if __name__ == '__main__':
    parser = optparse.OptionParser(usage="%prog [options] listen_port")
    parser.add_option("--verbose", "-v", action="store_true",
                      help="verbose messages and per frame traffic")
    parser.add_option("--cert", default="self.pem",
                      help="SSL certificate file")
    parser.add_option("--key", default=None,
                      help="SSL key file (if separate from cert)")
    parser.add_option("--ssl-only", action="store_true",
                      help="disallow non-encrypted connections")
    (opts, args) = parser.parse_args()

    try:
        if len(args) != 1:
            raise ValueError
        opts.listen_port = int(args[0])
    except ValueError:
        parser.error("Invalid arguments")

    logging.basicConfig(level=logging.INFO)

    opts.web = "."
    server = WebSockifyServer(WebSocketEcho, **opts.__dict__)
    server.start_server()
