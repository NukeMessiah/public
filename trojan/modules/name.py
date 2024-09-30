#!/usr/bin/python3
#This module retrieves the Operating System name running on the remote machine on which the trojan is executing
#and returns the base64-encoded string.

import os

def run(**args):
    print("[*] In name module.")
    return os.name