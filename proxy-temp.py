import argparse
from socket import socket, AF_INET, SOCK_STREAM

ENCODING = "utf-8"

def parse_request(request):
    lines = [line for line in request.decode(ENCODING).split("\r\n") if line]
    method, uri_and_port, version = lines[0].split()
    uri, port = uri_and_port.split(":")

    headers = dict()
    for line in lines[1:]:
        key, value = line.split(": ")
        headers[key] = value

    return method, uri, port, version, headers

def process_request(request, serverSocket):
    method, uri, port, version, headers = parse_request(request)
    print(method)
    print(uri)
    print(port)
    print(version)
    print(headers)

    # initiate connection with webserver
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((headers['host'], port))
    try:
        client.Socket.send(request)
    except Exception as e:
        client.Socket.close()
    # reply client on connection status


    # get resource request from client

    # send resouce request to server
     
    # get response from server
    
    # send resource to client 
    clientSocket.close()

def main():
    # parse arguments: port, flag_telemetry, filename of blacklists
    parser = argparse.ArgumentParser()
    parser.add_argument('port', type=int, help="port number")
    parser.add_argument('flag_telemetry', nargs="?", type=bool, help="flag for telemetry") # remove narg
    parser.add_argument('filename of blacklists', nargs="?", help="filename for blacklists") # remove narg
    args = parser.parse_args()
    serverPort = args.port

    # create socket and wait for request
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('', serverPort))
    serverSocket.listen(1)
    print("The server is ready to receive")


    connectionSocket, clientAddress = serverSocket.accept()
    request = connectionSocket.recv(1024)
    try:
        process_request(request, connectionSocket)
    except Exception as e:
        print(e)
        connectionSocket.close()
        serverSocket.close()
    
    connectionSocket.close()
    serverSocket.close()




main()





