# -*- coding: utf-8 -*-
import argparse
import sys
import socket
import select
import threading
import time
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from http import HTTPStatus
import http.client

ENABLE_TELEMETRY = 1
DISABLE_TELEMETRY = 0
NUM_THREADS = 8
CONNECTION_TIMEOUT = 5
BUFFER_SIZE = 8192

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):

    address_family = socket.AF_INET
    daemon_threads = True
    sem = threading.Semaphore(NUM_THREADS)

    def __init__(self, flag_telemetry, blacklists, *args, **kwargs):
        self.flag_telemetry = flag_telemetry
        self.blacklists = blacklists

        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        sys.stdout.write(format%args)
        sys.stdout.flush()

    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self)

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)
            self.sem.release()

    def process_request(self, request, client_address):

        self.sem.acquire()
        t = threading.Thread(target = self.process_request_thread,
                             args = (request, client_address))
        t.daemon = self.daemon_threads
        self._threads.append(t)
        t.start()

class ProxyRequestHandler(BaseHTTPRequestHandler):
    timeout = CONNECTION_TIMEOUT
    lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        self.flag_telemetry = args[2].flag_telemetry
        self.blacklists = args[2].blacklists

        self.tls = threading.local()
        self.tls.conns = {}

        super().__init__(*args, **kwargs)

    def log_error(self, format, *args):
        pass
        # surpress "Request timed out: timeout('timed out',)"
        # if isinstance(args[0], socket.timeout):
        #     return
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
        # port is definitely 443 because we only use https
        address[1] = 443
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
        breakWhileLoop = False
        while not breakWhileLoop:
            rlist, wlist, xlist = select.select(conns, [], conns, self.timeout)
            if xlist or not rlist:
                break
            for r in rlist:
                other = conns[1] if r is conns[0] else conns[0]
                try:
                    data = r.recv(BUFFER_SIZE)
                except ConnectionResetError as e:
                    breakWhileLoop = True
                    break
                if r == conns[1]:
                    size += sys.getsizeof(data)
                if not data:
                    breakWhileLoop = True
                    break
                other.sendall(data)
        duration = time.time() - start_time
        self.log_request(size, duration)

    def parse_request(self):
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version
        self.close_connection = True
        requestline = str(self.raw_requestline, 'iso-8859-1')
        requestline = requestline.rstrip('\r\n')
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 0:
            return False

        self.protocol_version = self.requestline.split()[-1]

        if len(words) >= 3:  # Enough to determine protocol version
            version = words[-1]
            try:
                if not version.startswith('HTTP/'):
                    raise ValueError
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                # RFC 2145 section 3.1 says there can be only one "." and
                #   - major and minor numbers MUST be treated as
                #      separate integers;
                #   - HTTP/2.4 is a lower version than HTTP/2.13, which in
                #      turn is lower than HTTP/12.3;
                #   - Leading zeros MUST be ignored by recipients.
                if len(version_number) != 2:
                    raise ValueError
                version_number = int(version_number[0]), int(version_number[1])
            except (ValueError, IndexError):
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    "Bad request version (%r)" % version)
                return False
            if version_number >= (1, 1) and self.protocol_version >= "HTTP/1.1":
                self.close_connection = False
            if version_number >= (2, 0):
                self.send_error(
                    HTTPStatus.HTTP_VERSION_NOT_SUPPORTED,
                    "Invalid HTTP version (%s)" % base_version_number)
                return False
            self.request_version = version

        if not 2 <= len(words) <= 3:
            self.send_error(
                HTTPStatus.BAD_REQUEST,
                "Bad request syntax (%r)" % requestline)
            return False
        command, path = words[:2]
        if len(words) == 2:
            self.close_connection = True
            if command != 'GET':
                self.send_error(
                    HTTPStatus.BAD_REQUEST,
                    "Bad HTTP/0.9 request type (%r)" % command)
                return False
        self.command, self.path = command, path

        # Examine the headers and look for a Connection directive.
        try:
            self.headers = http.client.parse_headers(self.rfile,
                                                     _class=self.MessageClass)
        except http.client.LineTooLong as err:
            self.send_error(
                HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
                "Line too long",
                str(err))
            return False
        except http.client.HTTPException as err:
            self.send_error(
                HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
                "Too many headers",
                str(err)
            )
            return False

        conntype = self.headers.get('Connection', "")
        if conntype.lower() == 'close':
            self.close_connection = True
        elif (conntype.lower() == 'keep-alive' and
              self.protocol_version >= "HTTP/1.1"):
            self.close_connection = False
        # Examine the headers and look for an Expect directive
        expect = self.headers.get('Expect', "")
        if (expect.lower() == "100-continue" and
                self.protocol_version >= "HTTP/1.1" and
                self.request_version >= "HTTP/1.1"):
            if not self.handle_expect_100():
                return False
        return True

    def send_response(self, code, message=None):
        self.send_response_only(code, message)
        self.send_header('Server', self.version_string())
        self.send_header('Date', self.date_time_string())

    def log_request(self, size='-', duration='-'):
        self.log_message('Hostname: %s, Size: %s bytes, Time: %.3f sec\n',
                         self.headers["Host"].split(":", 1)[0],
                         str(size), duration)

    def log_message(self, format, *args):
        if self.flag_telemetry == ENABLE_TELEMETRY:
            sys.stdout.write(format%args)
            sys.stdout.flush()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help="port number")
    parser.add_argument('flag_telemetry', type=int,
        choices=[ENABLE_TELEMETRY, DISABLE_TELEMETRY],
        help="flag for telemetry")
    parser.add_argument('filename_of_blacklists',
        help="filename for blacklists")
    args = parser.parse_args()

    return args.port, args.flag_telemetry, args.filename_of_blacklists

def load_blacklists(filename_of_blacklists):
    blacklists = None
    if filename_of_blacklists:
        try:
            with open(filename_of_blacklists, 'r') as f:
                blacklists = set([line[:-1] for line in f.readlines()])
        except FileNotFoundError:
            print("Blacklists file was not found.")
            exit(0)
    return blacklists or set()

def get_server_address(port):
    # '' binds to all interfaces
    return ('', port)

def main():
    port, flag_telemetry, filename_of_blacklists = parse_args()
    blacklists = load_blacklists(filename_of_blacklists)
    server_address = get_server_address(port)
    httpd = ThreadingHTTPServer(flag_telemetry, blacklists, server_address,
        ProxyRequestHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Keyboard interrupt received.")
        sys.exit(0)

if __name__ == '__main__':
    main()
