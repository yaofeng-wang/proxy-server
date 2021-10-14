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

ENABLE_TELEMETRY = 1
DISABLE_TELEMETRY = 0
NUM_THREADS = 8
CONNECTION_TIMEOUT = 5
BUFFER_SIZE = 8192

# need to use the correct HTTP version
HTTP_VERSION = "HTTP/1.1"
# HTTP_VERSION = "HTTP/1.0"

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
        self.close_connection = 0
        while not self.close_connection:
            rlist, wlist, xlist = select.select(conns, [], conns, self.timeout)
            if xlist or not rlist:
                break
            for r in rlist:
                other = conns[1] if r is conns[0] else conns[0]
                try:
                    data = r.recv(BUFFER_SIZE)
                except ConnectionResetError as e:
                    self.close_connection = 1
                    break
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

def main(HandlerClass=ProxyRequestHandler,
    ServerClass=ThreadingHTTPServer,
    protocol=HTTP_VERSION):

    port, flag_telemetry, filename_of_blacklists = parse_args()
    blacklists = load_blacklists(filename_of_blacklists)
    server_address = get_server_address(port)
    HandlerClass.protocol_version = protocol
    httpd = ServerClass(flag_telemetry, blacklists, server_address, HandlerClass)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Keyboard interrupt received.")
        sys.exit(0)

if __name__ == '__main__':
    main()
