import sys
import webbrowser
import keyboard
import time
import itertools
import threading


def get_commit_file_path() -> str:
    if get_os() == "windows":
        return "C:\\.gd\\.commit-msg"

def get_os():
    if sys.platform == "win32":
        return "windows"

def open_browser(url):
    print("[¤] press any key to open repository in your browser or q to quit the program.")
    if keyboard.read_key() == "q":
        sys.exit(0)
    else:
        webbrowser.open(url)

class Loading:
    def __init__(self, type: ["dots","dynamic"]="dots", start_text="Processing", stop_text: str="Done", 
                 list_: list=["/", "|", "\\", "-"], timeout:float=0.5):
        self.type = type
        self.start_text = start_text
        self.stop_text = stop_text
        self.timeout = timeout
        if self.type == "dots":
            self.list_ = [ "", "." , ".." , "..."]
        elif self.type == "dynamic":
            self.list_ = list_
        else:
            raise "Invalid Type"
    
    def start(self):
        self.done = False
        thread = threading.Thread(target=self.__loop)
        thread.daemon = True
        thread.start()
    
    def __loop(self):
        if self.type == "dots":
            for i in itertools.cycle(self.list_):
                if self.done:
                    break
                print("\r"+self.start_text + i+" "*(len(self.list_)-self.list_.index(i)-1),end="",flush=True)
                time.sleep(self.timeout)
            
        elif self.type == "dynamic":
            for i in itertools.cycle(self.list_):
                if self.done:
                    break
                print("\r"+self.start_text,i,end="",flush=True)
                time.sleep(self.timeout)

    def stop(self):
        self.done = True
        if self.type == "dots":
            print("\r"+self.stop_text+" "*(len(self.start_text)+len(self.list_)-len(self.stop_text)))
        elif self.type == "dynamic":
            print("\r"+self.stop_text+" "*(len(self.start_text)+2-len(self.stop_text))+"\r")
    
    def abort(self):
        self.done = True
        print("\r")
