#!/usr/bin/env python3

import argparse
import logging
import os
import re
import subprocess
import tempfile
import time
import unittest
# import wormgate
import requests

opts_to_pipe_output = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
        }


def create_http_URL(address, header=""):
    return f"http://{address}/{header}"


def setup_worm():
    with open("segment.bin", "rb") as file:
        data = file.read()

    wormgate_URL    = create_http_URL(f"{args.host}:{args.port}")
    response    = requests.post(wormgate_URL+f'worm_entrance?args={1}-{1}', data=data)
    time.sleep(1)


def test_grow_worm():
    wormgate_URL    = create_http_URL(f"{args.host}:{args.port}")
    leader_URL      = create_http_URL(f"{args.host}:{args.port + 1}")

    try:
        response    = requests.post(f"{leader_URL}set_max_segments/{1}")
        print(response)
        start_time = time.time()
        response    = requests.post(f"{leader_URL}set_max_segments/{20}")
        print(f"grow_time : {time.time() - start_time}")
        print(response)
    finally:
        response    = requests.post(f"{leader_URL}set_max_segments/{1}")
        

def test_shrink_worm():
    wormgate_URL    = create_http_URL(f"{args.host}:{args.port}")
    leader_URL      = create_http_URL(f"{args.host}:{args.port + 1}")

    try:
        response    = requests.post(f"{leader_URL}set_max_segments/{10}")
        print(response)
        start_time = time.time()
        response    = requests.post(f"{leader_URL}set_max_segments/{1}")
        print(f"shrink_time : {time.time() - start_time}")
        print(response)
    finally:
        response    = requests.post(f"{leader_URL}set_max_segments/{1}")




def build_arg_parser():
    parser = argparse.ArgumentParser(prog="test_segment.py")

    parser.add_argument("-c", "--host", type=str)
    parser.add_argument("-p", "--port", type=int)

    return parser

if __name__ == "__main__":
    parser = build_arg_parser()
    global args
    args = parser.parse_args()
    print(args)

    setup_worm()
    test_grow_worm()
    test_shrink_worm()

