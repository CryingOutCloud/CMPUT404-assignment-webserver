#  coding: utf-8 
import socketserver
import os
from urllib.parse import urlparse
from pathlib import Path

# Copyright 2023 Noah Batiuk

# Adapted from Abram Hindle, Eddie Antonio Santos, 2013
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):
    
    # https://gist.github.com/HaiyangXu/ec88cbdce3cdbac7b8d5
    extensions_map={
        'manifest': 'text/cache-manifest',
        'html': 'text/html',
        'png': 'image/png',
        'jpg': 'image/jpg',
        'svg':	'image/svg+xml',
        'css':	'text/css',
        'js':	'application/x-javascript',
        '': 'application/octet-stream', # Default
    }

    # Main loop of program
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print ("Got a request of: %s\n" % self.data)

        # Ignore empty requests
        if self.data != b'':

            self.base = 'www'
            self.parse_request()
            
            # Send a 405 response for methods we can't handle
            if not self.valid_method():

                header = "HTTP/1.1 405 Method Not Allowed\n\n"
                response = ''
                # response = '<html><body><center><h3>Error 405: Method not allowed</h3></center></body></html>' #.encode('utf-8')
                self.send_response(header, response)

            else:
                self.file_path = os.path.join(self.base, self.caller_file)
                print(1, self.file_path)

                self.url_too_deep()

                # Check to see if page exists
                try:
                    print("\n\n", self.file_path, os.path.exists(self.file_path))
                    if not os.path.exists(self.file_path):
                        raise FileNotFoundError

                    if self.url_too_deep():
                        raise FileNotFoundError

                except Exception as e:
                    print("File not found")
                    # if self.file_path == 'www/favicon.ico':
                    #     pass
                    # else:
                    header = "HTTP/1.1 404 Not Found\n\n"
                    response = '<html><body><center><h3>Error 404: File not found</h3></center></body></html>' #.encode('utf-8')
                    self.send_response(header, response)

                else:

                    if self.validate_path():

                        # https://stackoverflow.com/questions/70998506/how-to-respond-to-a-get-request-for-favicon-ico-in-a-local-webserver-using-socke
                        if self.file_path == 'www/favicon.ico':
                            with open(self.file_path, "rb") as f:
                                ico = f.read()
                            response = f"HTTP/1.1 200 OK\r\nContent-Type: image/x-icon\r\nContent-Length: {len(ico)}\r\n\r\n" 
                            self.request.sendall((response).encode())

                        else:    
                            extension = self.file_path.split('.')[1]
                            content_type = self.extensions_map[extension]
                            header = f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\n\n"

                            # https://www.codementor.io/@joaojonesventura/building-a-basic-http-server-from-scratch-in-python-1cedkg0842
                            with open(self.file_path) as f:
                                response = f.read()

                            self.send_response(header, response)
                            

    # emalsha.wordpress.com/2016/11/24/how-create-http-server-using-python-socket-part-ii
    def parse_request(self):

        parts = str(self.data).split(' ')
        self.method = parts[0][2:]
        self.caller_file = parts[1].lstrip('/')
        print("file: ", self.caller_file)


    def valid_method(self):
        if self.method == "GET":
            return True
        else:
            return False


    def send_response(self, header, page=''):
        self.request.sendall((header + page).encode())


    def validate_path(self):
        if self.file_path.endswith('/') and os.path.isdir(self.file_path):
            print("Ends with /")
            self.file_path += 'index.html'
            return True
        elif self.file_path == (self.base + '/'):
            print("Base folder")
            self.file_path = os.path.join(self.base, 'index.html')
            return True
        elif not self.file_path.endswith('/') and os.path.isdir(self.file_path):
            redirect_path = self.caller_file + '/'
            print("\n\nredirect path:", redirect_path)
            header = f"HTTP/1.1 301 Moved Permanently\r\nLocation: http://127.0.0.1:8080/{redirect_path}\n\n"
            self.send_response(header)

            return False

        else:
            self.file_path = self.file_path.strip('/')

            return True


    # https://stackoverflow.com/questions/3812849/how-to-check-whether-a-directory-is-a-sub-directory-of-another-directory
    def url_too_deep(self):

        # Gets full path for both base and url
        parent_path = os.path.abspath(self.base)
        child_path = os.path.abspath(self.file_path)

        # See if base is alon the path for self.file_path
        common = os.path.commonpath([parent_path]) == os.path.commonpath([parent_path, child_path])
        print("Is parent: ", common)

        return not common




if __name__ == "__main__":
    HOST, PORT = "127.0.0.1", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
