#!/usr/bin/env python3
import requests
import time
import json
from os import sys
import socket
import http.server
import socketserver
import threading
import random

def create_neighbour(address, id):
    return {
        "address"   : address,
        "id"        : int(id)
    }

def create_http_URL(address, header=""):
    return f"http://{address}/{header}"

def create_thread(function):
    function_thread         = threading.Thread(target=function)
    function_thread.daemon  = True
    function_thread.start()

    return function_thread

class HttpRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def send_whole_response(self, code, content, content_type=None):
        if isinstance(content, str):
            content = content.encode("utf-8")
            if not content_type:
                content_type = "text/plain"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"
                
        elif isinstance(content, object):
            content         = json.dumps(content, indent=2)
            content         += "\n"
            content         = content.encode("utf-8")
            content_type    = "application/json"

        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length',len(content))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        parsed_path     = self.path.split("/")
        content_length  = int(self.headers.get('content-length', 0))
        content         = self.rfile.read(content_length)

        if parsed_path[1] == "kill":
            self.send_whole_response(200, "KILL")
            segment.shutdown()

        elif parsed_path[1] == "join":
            neighbour = create_neighbour(parsed_path[2], parsed_path[3])
            segment.post_join(neighbour)
            self.send_whole_response(200, "JOIN")

        elif parsed_path[1] == "set_max_segments":
            segment.set_max_segments(int(parsed_path[2]))
            while(segment.max_segments != len(segment.neighbours) + 1):
                pass
            self.send_whole_response(200, f"SET MAX SEGMENTS TO {parsed_path[2]}")

        else:
            self.send_whole_response(400, "Unknown path: " + self.path)

    def do_GET(self):
        if self.path == "/segment_info":
            self.send_whole_response(200, segment.get_info())

        else:
            self.send_whole_response(404, "Unknown path: " + self.path)


class ThreadingHttpServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, id, addr, gate, max_segments, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id             = id
        self.addr           = addr
        self.max_segments   = max_segments
        self.num_segments   = 1

        if(self.id == 1):
            self.leader = True
        else:
            self.leader = False

        self.numsegments    = 0
        self.neighbours     = []

        self.gates = set()
        self.gates.update([gate+":50000"])


    def get_info(self):
        return {
            "segment_addr"      : self.addr,
            "neighbours"        : self.neighbours,
            "id"                : self.id,
            "gates"             : list(self.gates),
            "leader"            : self.leader,
            "max_segments"      : self.max_segments,
            "num_segments"      : self.num_segments
        }
    
    def set_max_segments(self, max_segments): 
        if(max_segments >= 1):
            self.max_segments = max_segments
        else:
            print("Cannot set max_segments to less than 1!")

    def remove_neighbour(self, neighbour):
        try:
            self.neighbours.remove(neighbour)
        except:
            print(f"Neighbour: {neighbour} already removed!")

        self.num_segments = len(self.neighbours) + 1

    def add_neighbour(self, neighbour):
        self.neighbours.append(neighbour)
        self.num_segments   = len(self.neighbours) + 1

        try:
            URL = create_http_URL(neighbour['address'], f"join/{self.addr}/{self.id}")
            res = requests.post(url = URL)
        except:
            self.remove_neighbour(neighbour)

    def post_join(self, new_neighbour):
        if new_neighbour['address'] != self.addr:
            if not any(neighbour['address'] == new_neighbour['address'] for neighbour in self.neighbours):
                self.add_neighbour(new_neighbour)

    def elect_new_leader(self):
        if not any(int(neighbour['id']) < self.id for neighbour in self.neighbours):
            self.leader = True

    def ping_segments(self):
        time.sleep(10)
        for neighbour in self.neighbours:
            try:
                URL = create_http_URL(neighbour['address'], "segment_info")
                res = requests.get(url = URL).json()
                
                if(res['leader']):
                    self.max_segments = res['max_segments']

                for s in res["neighbours"]:
                    self.post_join(s)
            except requests.exceptions.RequestException:
                self.remove_neighbour(neighbour)
                if(int(neighbour['id']) < self.id):
                    self.elect_new_leader()
        

    def worm_get_info(self, URL):
        res = requests.get(url = URL+"info").json()

        try:
            self.gates.update(res['other_gates'])
        except:
            print(f"Wormgate {res['servername']} does not have other_gates!")
        finally:
            return res

    def find_new_id(self):
        new_id = int(self.id)
        for neighbour in self.neighbours:
            if(new_id < int(neighbour['id'])):
                new_id = int(neighbour['id'])

        return new_id + 1
    
    def segment_kill(self):
        random_neighbour = random.choice(self.neighbours)
        try:
            URL         = create_http_URL(random_neighbour['address'], "kill")
            response    = requests.post(URL)
        except:
            print(f"Segment: {random_neighbour} already killed!")
        finally:
            self.remove_neighbour(random_neighbour)


    def worm_post_segment(self, addr):
        URL         = create_http_URL(addr)
        new_id      = self.find_new_id()

        response    = requests.post(URL+f'worm_entrance?args={new_id}-{self.max_segments}', data=data)
        time.sleep(0.3)
        
        new_segment_port    = str(gate_port + new_id)
        new_neighbour       = create_neighbour(addr.split(":")[0] +":"+ new_segment_port, new_id)
        self.add_neighbour(new_neighbour)


def run_http_server():
    gate_name   = socket.gethostbyaddr(socket.gethostname())[1][0]
    global gate_port
    gate_port   = 50000
    gate_URL    = create_http_URL(f"{gate_name}:{gate_port}")

    global data
    with open(sys.argv[0], 'rb') as file:
        data = file.read()

    args            = sys.argv[1].split("-")
    segment_id      = int(args[0])
    max_segments    = int(args[1])

    segment_port    = gate_port + segment_id
    segment_addr    = f"{gate_name}:{segment_port}"

    global segment
    segment = ThreadingHttpServer(segment_id, segment_addr, gate_name, max_segments, (gate_name, segment_port), HttpRequestHandler)

    def segment_main():
        segment.serve_forever()

    def create_segments():
        res = segment.worm_get_info(gate_URL)
        while(True):
            if(segment.leader == True): 
                for gate in segment.gates:
                    if(len(segment.neighbours) + 1 < segment.max_segments):
                        url = create_http_URL(gate)
                        res = segment.worm_get_info(url)
                        # if(res['numsegments'] < 2):
                        segment.worm_post_segment(gate)
                    elif(len(segment.neighbours) + 1 > segment.max_segments):
                        segment.segment_kill()
            # else:
            #     segment.ping_segments()


    def ping_segments():
        while(True):
            segment.ping_segments()

    ping_segments_thread    = create_thread(ping_segments)
    main_thread             = create_thread(segment_main)
    create_segments_thread  = create_thread(create_segments)

    main_thread.join()
    if main_thread.is_alive():
        segment.shutdown()

if __name__ == '__main__':
    run_http_server()