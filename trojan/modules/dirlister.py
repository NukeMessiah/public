#!/usr/bin/python3
#This module lists all of the files in the current directory on the target machine and return it as a base64-encoded string.
import os

def run(**args):
    print("[*] In dirlister module.")
    files = os.listdir(".")
    return str(files)