import sys, inquirer, os, itertools, time, threading, PyInquirer
from inquirer.themes import ThemeError

from subprocess import Popen, PIPE, DEVNULL


def listPromptInquirer(*dict_):
    # dict_ should be in this format: { "name": "", "question":"", "choices":[], "default":"" }
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
    # dict_ should be in this format: { "name": "", "question":"", "choices":[], *"default":"", *"validate" = validate }
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

def promptPyInquirer(*dict_):
    # dict_ should be in this format: { "type": "", "name": "", "message":"", "choices":[], "default":"", "validate": lambda }
    # type can be: "input", "list", "checkbox", "confirm", "password"
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
            if(q["type"] == "list"):
                tempDict["choices"] = q["choices"]
            questions.append(tempDict)
        else:
            tempDict = {
                    "type": q["type"],
                    "name": q["name"],
                    "message":q["message"],
                    "default":q["default"] if "default" in q else "",
            }
            if(q["type"] == "list"):
                tempDict["choices"] = q["choices"]
            questions.append(tempDict),
    try:
        answer = PyInquirer.prompt(questions)
        for q in dict_ :
            answer[q["name"]]
        return answer
    except(TypeError, KeyError, KeyboardInterrupt):
        print("Error: the program has been interrupted.")
        sys.exit(10)

# promptPyInquirer({
#     "type":"input",
#     "name": "path",
#     "message": "path plz?",
#     "validate": lambda x: "Invalid path" if not os.path.exists(x) else True
# })

def invalidAnswerExit():
    print("invalid answer")
    sys.exit(12)

def defaultCommit(args):
    path = args["path"]
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
        cmds.append(f"git commit -m \"{commit_msg}\"")
    for cmd in cmds:
        runCmd(cmd, stdout=PIPE, stderr=PIPE)

def handleGitInit(path):
    files_dirs = os.listdir(path)
    if ".git" not in files_dirs:
        runCmd("git init", stdout=PIPE, stderr=PIPE)

def openBash(input_, **std):
    stdin = std["stdin"] if "stdin" in std else PIPE
    stdout = std["stdout"] if "stdout" in std else None
    stderr = std["stderr"] if "stderr" in std else None
    error = std["error"] if "error" in std else "an error has been caught\n"
    returncode = std["returncode"] if "returncode" in std else False
    printBashError = std["printBashError"] if "printBashError" in std else True
    load = std["load"] if "load" in std else None
    timeout = std["timeout"] if "timeout" in std else None
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
            if load:
                load.abort()
            if printBashError:
                print(error+"\n",err.decode() if err else "",sep="")
            else:
                print(error)
            sys.exit(5)
        return out.decode() if out else out

def runCmd(cmd, **std):
    stdin = std["stdin"] if "stdin" in std else None
    stdout = std["stdout"] if "stdout" in std else None
    stderr = std["stderr"] if "stderr" in std else None
    error = std["error"] if "error" in std else "an error has been caught\n"
    timeout = std["timeout"] if "timeout" in std else None
    process = Popen(cmd, shell=True, stdin=stdin, stderr=stderr, stdout=stdout)
    out, err = process.communicate()
    if timeout:
        process.wait(timeout=timeout)
    elif not timeout:
        process.wait()
    if process.returncode != 0:
        print(error)
        print(err.decode()) if err else ""
        sys.exit(10)
        return None
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
    print("*")
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