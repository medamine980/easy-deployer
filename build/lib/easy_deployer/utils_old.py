import sys, inquirer, os, itertools, time, threading, PyInquirer

from subprocess import Popen, PIPE, DEVNULL



def listPromptInquirer(*dict_):
    """dict_ should be in this format:
    { 
        "name": str, 
        "question":str, 
        "choices": list, 
        "default": str
    }""" 
    questions = []
    for q in dict_:
        if("validate" in q):
            questions.append(
            inquirer.List(q["name"],
                    message=q["question"],
                    choices=q["choices"],
                    default=q["default"] if "default" in q else "",
                    validate=q["validate"]
                ),
            )
        else:
            questions.append(
            inquirer.List(q["name"],
                    message=q["question"],
                    choices=q["choices"],
                    default=q["default"] if "default" in q else "",
                    
                ),
            )
    try:
        answer = inquirer.prompt(questions)
        for q in dict_ :
            answer[q["name"]]
        return answer
    except(TypeError, KeyError, KeyboardInterrupt):
        print("Error: the program has been interrupted.")
        sys.exit(10)

def checkBoxPromptInquirer(*dict_):
    """dict_ should be in this format: 
        { 
            "name": str, 
            "question": str, 
            "choices": list, 
            *"default": str,
            *"validate" = lambda
        }"""
    questions = []
    for q in dict_:
        if("validate" in q):
            questions.append(
            inquirer.Checkbox(q["name"],
                    message=q["question"],
                    choices=q["choices"],
                    default=q["default"] if "default" in q else "",
                    validate=q["validate"]
                ),
            )
        else:
            questions.append(
            inquirer.Checkbox(q["name"],
                    message=q["question"],
                    choices=q["choices"],
                    default=q["default"] if "default" in q else ""
                ),
            )
    try:
        answer = inquirer.prompt(questions)
        for q in dict_ :
            answer[q["name"]]
        return answer
    except(TypeError, KeyError, KeyboardInterrupt):
        print("Error: the program has been interrupted.")
        sys.exit(10)

def textPromptInquirer(*dict_):
    # dict_ should be in this format: { "name": "", "question":"", "default":"" }
    questions = []
    for q in dict_:
        if("validate" in q):
            questions.append(
            inquirer.Text(q["name"],
                    message=q["question"],
                    default=q["default"] if "default" in q else "",
                    validate=q["validate"]
                ),
            )
        else:
            questions.append(
            inquirer.Text(q["name"],
                    message=q["question"],
                    default=q["default"] if "default" in q else "",
                ),
            )
    try:
        answer = inquirer.prompt(questions)
        for q in dict_ :
            answer[q["name"]]
        return answer
    except(TypeError, KeyError, KeyboardInterrupt):
        print("Error: the program has been interrupted.")
        sys.exit(10)

def take_input():
    pass

def promptPyInquirer(*dict_) -> dict:
    """
    * dict_ should be in this format: { "type": "", "name": "", "message":"", "choices":[], "default":"", "validate": lambda }
    * type can be: "input", "list", "checkbox", "confirm", "password" """
    # 'validate': lambda val: 'Input should not be empty' if len(val) == 0 else True,
    questions = []
    for q in dict_:
        if("validate" in q):
            tempDict = {
                    "type": q["type"],
                    "name": q["name"],
                    "message":q["message"],
                    "default":q["default"] if "default" in q else "",
                    "validate": q["validate"]
            }
            if(q["type"] == "list" or q["type"] == "checkbox"):
                tempDict["choices"] = q["choices"]
            if "default" in q and q["type"] != "checkbox":
                tempDict["default"] = q["default"]
            questions.append(tempDict)
        else:
            tempDict = {
                    "type": q["type"],
                    "name": q["name"],
                    "message":q["message"],
            }
            if(q["type"] == "list" or q["type"] == "checkbox"):
                tempDict["choices"] = q["choices"]
            if "default" in q and q["type"] != "checkbox":
                tempDict["default"] = q["default"]
            questions.append(tempDict)
    try:
        answer = PyInquirer.prompt(questions)
        for q in dict_ :
            answer[q["name"]]
        return answer
    except(TypeError, KeyError, KeyboardInterrupt):
        print("Error: the program has been interrupted.")
        sys.exit(10)


def invalidAnswerExit():
    print("invalid answer")
    sys.exit(12)

def defaultCommit(args:dict):
    """This function handles default commits, (git add ., git commit -m "message")"""
    path = args["path"]
    os.chdir(path)
    cmds = []
    handleGitInit(path)
    isCommitNeeded = checkCommit()
    if isCommitNeeded:
        cmds += [
        "git add ."
        ]
        commit_msg = input("commit message (double quotes are not allowed): ")
        if "\"" in commit_msg:
            print("double quotes detected, error!")
            sys.exit(15)
        cmds.append(f"git -C {path} commit -m \"{commit_msg}\"")
    
    for cmd in cmds:
        startText="processing"
        if cmds.index(cmd) == 0:
            # command is "git add ."
            startText="Adding files"
        elif cmds.index(cmd) == 1:
            # command is git commit
            startText="Committing changes"
        loading = Loading(startText=startText, stopText="", timeout=1)
        loading.start()
        runCmd(cmd, stdout=PIPE, stderr=PIPE, loading=loading)
        loading.stop()

def handleGitInit(path):
    files_dirs = os.listdir(path)
    if ".git" not in files_dirs:
        runCmd("git init", stdout=PIPE, stderr=PIPE)
# continue_ = promptPyInquirer({
#             "type":"confirm","name":"continue",
#             "message":"it seems like you've already committed your changes, still wanna push your files to heroku?"
#         })["continue"]
# print(continue_)
def openBash(input_, **options):
    stdin = options["stdin"] if "stdin" in options else PIPE
    stdout = options["stdout"] if "stdout" in options else None
    stderr = options["stderr"] if "stderr" in options else None
    error = options["error"] if "error" in options else "an error has been caught\n"
    returncode = options["returncode"] if "returncode" in options else False
    printBashError = options["printBashError"] if "printBashError" in options else True
    loading = options["loading"] if "loading" in options else None
    timeout = options["timeout"] if "timeout" in options else None
    os_ = getOS()
    if os_ == "windows":
        path = "C:\\Program Files\\Git\\bin\\bash.exe"
        process = Popen(path, stdin=stdin, stdout=stdout, stderr=stderr)
        out, err = process.communicate(input=input_.encode("utf-8"))
        if timeout:
            process.wait(timeout=timeout)
        elif not timeout:
            process.wait()
        if err and "command not found" in err.decode():
            print(err.decode())
            sys.exit(4)
        if returncode:
            out = out.decode() if out != None else out
            err = err.decode() if err != None else err
            return {"returncode":process.returncode,"out":out, "err":err}
        if process.returncode != 0:
            if loading:
                loading.abort()
            if printBashError:
                print(error+"\n",err.decode() if err else "",sep="")
            else:
                print(error)
            sys.exit(5)
        return out.decode() if out else out

def runCmd(cmd, **options):
    """
    * cmd (string): the command to be executed
    * options(dict):
            * stdin (None|PIPE)
            * stdout (None|PIPE)
            * error (str)
            * quitOnError (bool)
            * timeout (None|float)
            * loading (Loading)  
    """
    stdin = options["stdin"] if "stdin" in options else None
    stdout = options["stdout"] if "stdout" in options else None
    stderr = options["stderr"] if "stderr" in options else None
    error = options["error"] if "error" in options else "an error has been caught\n"
    quitOnError = options["quitOnError"] if "quitOnError" in options else True
    timeout = options["timeout"] if "timeout" in options else None
    loading:Loading = options["loading"] if "loading" in options else None
    process = Popen(cmd, shell=True, stdin=stdin, stderr=stderr, stdout=stdout)
    out, err = process.communicate()
    if timeout:
        process.wait(timeout=timeout)
    elif not timeout:
        process.wait()
    if process.returncode != 0 and quitOnError:
        if loading:
            loading.abort()
        print(error)
        print(err.decode()) if err else ""
        sys.exit(10)
    return out.decode() if out != None else None

def checkSoftware(name, cmd, url=None):
    err = f"It seems that {name} is not in your machine, please make sure to download it first"
    err += f"\n you can find it at {url}" if url else ""
    runCmd(cmd, stdout=DEVNULL,
        error= err
    )

def checkCommit():
    out = runCmd("git status", stdout=PIPE, stderr=PIPE)
    if "nothing to commit, working tree clean" in out:
        print(out)
        return False
    return True

def masterToMain():
    out = runCmd("git branch", stdout=PIPE, stderr=PIPE)
    if "main" in out:
        return
    runCmd("git branch -m master main", stdout=PIPE, stderr=PIPE)
    runCmd("git checkout main", stdout=DEVNULL, stderr=PIPE)

def printWarning(*text,**keywords):
    print("""
    ******************************************
                  _   __               __    
        \  /\  / /_\ |__| |\ | | |\ | |  __
         \/  \/ /   \|  \ | \| | | \| |__|  """)
    print("\t",*text, **keywords)
    print("""
    *******************************************""")

def getOS():
    if sys.platform == "win32":
        return "windows"

class Loading:
    def __init__(self,**info):
        self.type = info["type"] if "type" in info else "dots"
        self.startText = info["startText"] if "startText" in info else "Processing"
        self.stopText = info["stopText"] if "stopText" in info else "Done!"
        self.timeout = info["timeout"] if "timeout" in info else 0.5
        if self.type == "dots":
            self.list_ = [ "", "." , ".." , "..."]
        elif self.type == "dynamic":
            self.list_ = info["list_"] if "list_" in info else ["/", "|", "\\", "-"]
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
                print("\r"+self.startText + i+" "*(len(self.list_)-self.list_.index(i)-1),end="",flush=True)
                time.sleep(self.timeout)
            
        elif self.type == "dynamic":
            for i in itertools.cycle(self.list_):
                if self.done:
                    break
                print("\r"+self.startText,i,end="",flush=True)
                time.sleep(self.timeout)

    def stop(self):
        self.done = True
        if self.type == "dots":
            print("\r"+self.stopText+" "*(len(self.startText)+len(self.list_)-len(self.stopText)))
        elif self.type == "dynamic":
            print("\r"+self.stopText+" "*(len(self.startText)+2-len(self.stopText))+"\r")
    
    def abort(self):
        self.done = True
        print("\r")