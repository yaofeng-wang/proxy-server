# -*- coding: utf-8 -*-
import argparse
import sys
import os
import socket
import ssl
import select
import http.client
import urllib.parse
import threading
import gzip
import zlib
import time
import json
import re
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from io import StringIO
from html.parser import HTMLParser
from http import HTTPStatus


def with_color(c, s):
    return "\x1b[%dm%s\x1b[0m" % (c, s)

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):

    address_family = socket.AF_INET
    daemon_threads = True

    def __init__(self, flag_telemetry, blacklists, *args, **kwargs):
        self.flag_telemetry = flag_telemetry
        self.blacklists = blacklists

        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        sys.stderr.write(format%args)
        sys.stderr.flush()

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self)

class ProxyRequestHandler(BaseHTTPRequestHandler):
    timeout = 5
    lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        self.flag_telemetry = args[2].flag_telemetry
        self.blacklists = args[2].blacklists

        self.tls = threading.local()
        self.tls.conns = {}

        super().__init__(*args, **kwargs)

    def log_error(self, format, *args):
        # surpress "Request timed out: timeout('timed out',)"
        if isinstance(args[0], socket.timeout):
            return

        # self.log_message(format, *args)

    def dest_in_blacklists(self):
        for ipaddress in self.blacklists:
            dest_ipaddress = self.headers["Host"].split(":", 1)[0] 
            if ipaddress in dest_ipaddress:
                return True
        return False

    def do_CONNECT(self):
        if not self.dest_in_blacklists():
            self.connect_relay()
        else:
            self.send_error(HTTPStatus.NOT_FOUND)

    def connect_relay(self):
        address = self.path.split(':', 1)
        address[1] = int(address[1]) or 443
        try:
            s = socket.create_connection(address, timeout=self.timeout)
        except Exception as e:
            self.send_error(HTTPStatus.BAD_GATEWAY)
            return
        self.send_response(HTTPStatus.OK) 
        self.end_headers()

        start_time = time.time()
        size = 0
        conns = [self.connection, s]
        self.close_connection = 0
        while not self.close_connection:
            rlist, wlist, xlist = select.select(conns, [], conns, self.timeout)
            if xlist or not rlist:
                break
            for r in rlist:
                other = conns[1] if r is conns[0] else conns[0]
                data = r.recv(8192)
                size += sys.getsizeof(data)
                if not data:
                    self.close_connection = 1
                    break
                other.sendall(data)   
        duration = time.time() - start_time
        self.log_request(size, duration)

    def send_response(self, code, message=None):
        self.send_response_only(code, message)
        self.send_header('Server', self.version_string())
        self.send_header('Date', self.date_time_string())

    def log_request(self, size='-', duration='-'):
        self.log_message('Hostname: %s, Size: %s bytes, Time: %.3f sec\n',
                         self.headers["Host"].split(":", 1)[0], str(size), duration)

    def log_message(self, format, *args):
        sys.stderr.write(format%args)
        sys.stderr.flush()

    def relay_streaming(self, res):
        self.wfile.write("%s %d %s\r\n" % (self.protocol_version, res.status, res.reason))
        for line in res.headers.headers:
            self.wfile.write(line)
        self.end_headers()
        try:
            while True:
                chunk = res.read(8192)
                if not chunk:
                    break
                self.wfile.write(chunk)
            self.wfile.flush()
        except socket.error:
            # connection closed by client
            pass

    def filter_headers(self, headers):
        # http://tools.ietf.org/html/rfc2616#section-13.5.1
        hop_by_hop = ('connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade')
        for k in hop_by_hop:
            del headers[k]

        # accept only supported encodings
        if 'Accept-Encoding' in headers:
            ae = headers['Accept-Encoding']
            filtered_encodings = [x for x in re.split(r',\s*', ae) if x in ('identity', 'gzip', 'x-gzip', 'deflate')]
            headers['Accept-Encoding'] = ', '.join(filtered_encodings)

        return headers

    def encode_content_body(self, text, encoding):
        if encoding == 'identity':
            data = text
        elif encoding in ('gzip', 'x-gzip'):
            fio = StringIO()
            with gzip.GzipFile(fileobj=fio, mode='wb') as f:
                f.write(text)
            data = fio.getvalue()
        elif encoding == 'deflate':
            data = zlib.compress(text)
        else:
            raise Exception("Unknown Content-Encoding: %s" % encoding)
        return data

    def decode_content_body(self, data, encoding):
        if encoding == 'identity':
            text = data
        elif encoding in ('gzip', 'x-gzip'):
            fio = StringIO(data)
            with gzip.GzipFile(fileobj=fio) as f:
                text = f.read()
        elif encoding == 'deflate':
            try:
                text = zlib.decompress(data)
            except zlib.error:
                text = zlib.decompress(data, -zlib.MAX_WBITS)
        else:
            raise Exception("Unknown Content-Encoding: %s" % encoding)
        return text

    
    def print_info(self, req, req_body, res, res_body):
        pass
        

    def request_handler(self, req, req_body):
        pass

    def response_handler(self, req, req_body, res, res_body):
        pass

    def save_handler(self, req, req_body, res, res_body):
        self.print_info(req, req_body, res, res_body)


def parse_args():
    # parse arguments: port, flag_telemetry, filename of blacklists
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help="port number")
    parser.add_argument('flag_telemetry', nargs="?", type=bool, help="flag for telemetry") # remove narg
    parser.add_argument('filename_of_blacklists', nargs="?", help="filename for blacklists") # remove narg
    args = parser.parse_args()
    port = args.port
    flag_telemetry = args.flag_telemetry
    filename_of_blacklists = args.filename_of_blacklists
    return port, flag_telemetry, filename_of_blacklists

def main(HandlerClass=ProxyRequestHandler, ServerClass=ThreadingHTTPServer, 
    protocol="HTTP/1.1"):
    
    port, flag_telemetry, filename_of_blacklists = parse_args()

    blacklists = None
    if filename_of_blacklists:
        with open(filename_of_blacklists, 'r') as f:
            blacklists = set([line[:-1] for line in f.readlines()])
    
    server_address = ('', port)

    HandlerClass.protocol_version = protocol
    httpd = ServerClass(flag_telemetry, blacklists, server_address, HandlerClass)
    
    try: 
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        sys.exit(0)

if __name__ == '__main__':
    main()