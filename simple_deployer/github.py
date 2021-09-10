from subprocess import Popen, PIPE, DEVNULL
from argparse import ArgumentParser
import os, sys, json, getpass, re, time, itertools, threading, signal, webbrowser, keyboard

from shared_functions import printWarning, listPromptInquirer, promptPyInquirer, runCmd, getOS

def main():
    args = takeArgs() # Take the arguments
    if not os.path.exists(args["path"]):
        print("Invalid Path!")
        sys.exit(5)
    args["path"] = os.path.abspath(args["path"])
    args["path"] = args["path"].strip()
    checkSoftware("git", "git --help") # check if git is installed in the current machine
    args["path"] = os.path.abspath(args["path"]) # just changing 
    createResourceDir() #create resources
    # os.chdir(args["path"]) # changing directory
    if getOS() == "windows": # to clean the screen
        os.system("cls") #
    # if args["cmd"] == "add-to-path":
    #     add2Path(args)
    if args["git_ignore"]:
        handleGitIgnore(args["path"])
    if args["rm_git_ignore"]:
        handleRmGitIgnore(args["path"])
    if args["cmd"] == "update": # check if -u or --update is present when the user runs the script
        update(args)
        return
    if args["cmd"] == "delete":
        delete(args)
        return
    if args["cmd"] == "create-update":
        create_update(args)
        return

def takeArgs():
    parser = ArgumentParser(prog="github-deployer",
    usage="""You basically enter one of the following commands:
        ¤ create-update (which is the default one)
        ¤ update (to update an existing repository)
        ¤ delete (to delete an existing repository)
then you need to specify the path by using the -p or --path argument.""", description="%(prog)s <commands> [options]")
    parser.add_argument("-v","--version", action="version", version="version 1.0", help="%(prog)s current version")
    parser.add_argument("cmd", nargs="?", default="create-update", choices=["create-update", "update", "delete", "add-to-path"],help="commands, default command is 'create-update'")
    parser.add_argument("-p","--path", help="path of the folder intended to deploy.", required=True)
    parser.add_argument("-new", nargs="*", default=[], choices=["user","token"], help="if you want to resave user or token")
    parser.add_argument("-repo", "--repository",dest="name", help="repository name")
    parser.add_argument("-ac", "--add-collaborators", action="store_true",help="if you want to add collaborators, repository must exist to do so else you'll get an error")
    parser.add_argument("-visibility", action="store_true")
    # parser.add_argument("-atp","--add-to-path-var", action="store_true", help="if you want to add the program to path environnement variable so that you can run it wherever you are")
    parser.add_argument("-git-ig", "--git-ignore", action="store_true")
    parser.add_argument("-rm-git-ig", "--rm-git-ignore", action="store_true")
    args = parser.parse_args()
    return vars(args)

def create_update(args):
    infoAboutToken() # info telling the user that he needs a token to create a repository
    defaultCommit(args) # git add, git commit etc...
    username = handleUsername(args) # takes care of the username 
    token = handleToken(args, username) # takes care of the access token
    data = infoAboutRepo(username,token,args["name"],args["add_collaborators"], args["path"])
    url = getGithubUrl(data)
    createRepo = createRepository(url, token, args["path"])
    if createRepo:
        load = Loading(startText="Creating repository", stopText="repository has been created!", type="dynamic", timeout=.1)
        isCollaborators = data["collaborators"]
        data = {k:v for k,v in data.items() if k != "username" and k != "collaborators"}
        # cmd down is a command for creating a repository 
        load.start()
        cmd = 'curl -f -u :'+token+' https://api.github.com/user/repos -d \''+json.dumps(data)+'\' '
        out = openBash(cmd, stderr=PIPE ,stdout=PIPE, load=load, error="""Error has been caught:
            Authorization Required! check your username and password
        """, printBashError=False)
        load.stop()
        saveTokenIfnotSaved(token)
        if isCollaborators:
            handleCollaborators(username=username, token=token, name=data["name"])
    elif not createRepo:
        #if we don't need to create a repository (which means it's already available) then we simply print that below
        print("repository already exist...")
        if(args["visibility"]):
            if args["visibility"]:
                changeVisibility(username=username, token=token, name=data["name"])
        if(args["add_collaborators"]):
            handleCollaborators(username=username, token=token, name=data["name"])
    masterToMain(args["path"])
    addRemoteAndPush(url, args["path"])

def update(args):
    """
    it gets called when "-u" or "--update" are available
    it updates or (pushs) the specified directory to the specified repository
    """
    defaultCommit(args)
    username = handleUsername(args)
    token = handleToken(args, username)
    repo = getRepoName(args["name"])
    url = getGithubUrl({"username":username,"name":repo})
    if args["add_collaborators"]:
        addCollaborators(args, username=username, token=token, name=repo)
    if args["visibility"]:
        changeVisibility(username=username, token=token, name=repo)
    createRepo = createRepository(url,token, args["path"])
    saveTokenIfnotSaved(token)
    if createRepo:
        repoNotFoundError()
    elif not createRepo:
        masterToMain(args["path"])
        addRemoteAndPush(url, args["path"])

def delete(args):
    username = handleUsername(args)
    token = handleToken(args, username)
    repo = getRepoName(args["name"])
    url = getGithubUrl({ "username":username, "name":repo })
    createRepo = createRepository(url=url,token=token, path=args["path"])
    if createRepo:
        repoNotFoundError()
    elif not createRepo:
        load = Loading(startText="Deleting Repository",stopText="Repository Deleted", type="dynamic", timeout=.1)
        load.start()
        openBash(f"curl -X DELETE -H 'Authorization: token {token}' https://api.github.com/repos/{username}/{repo}", stdout=PIPE, stderr=PIPE ,load=load)
        load.stop()

def addCollaborators(args,**credentials):
    if not credentials:
        username = handleUsername(args)
        token = handleToken(args, username)
        repo = getRepoName(args["name"])
    elif credentials:
        username = credentials["username"]
        token = credentials["token"]
        repo = credentials["name"]
    url = getGithubUrl({"username": username, "name":repo})
    repositoryNeeded = createRepository(url, token, args["path"])
    if repositoryNeeded:
        print("ERROR\nRepository doesn't exist, check your repository name!")
        sys.exit(3)
    handleCollaborators(username=username, token=token, name=repo)
    

def add2Path(args):
    path = args["path"]
    if not os.path.isfile:
        print("Error, this is not a file!")
        sys.exit(3)
    if getOS() == "windows":
        if path in runCmd("echo %PATH%", stdout=PIPE, stderr=PIPE):
            print("It's Already in the path variable!")
            sys.exit(3)
        print("ok")
        runCmd('setx PATH "%PATH%;'+path+'"')


def cacheToken(username):
    key = input("Enter 'f' if you have access token in a file path, or 'c' if you have it on the clipboard: ").strip().lower()
    if key == 'f':
        fpath = input(f"Enter file path that contains the access token: (current directory {os.getcwd()}) ")
        if os.path.exists(fpath) and os.path.isfile(fpath):
            with open(fpath, 'r') as f:
                return f.read()
        elif os.path.exists(fpath) and not os.path.isfile(fpath):
            print("Error!", "This is not a file!")
            sys.exit(7)
        elif not os.path.exists(fpath):
            print("Error!","Invalid path!")
            sys.exit(7)
    elif key == 'c':
        return getpass.getpass("Enter host access token for user '"+username+"': ")
    else:
        invalidAnswerExit()
    

def promptCollaborators():
    isCollaborators = input("do you want collaborators with you in this repository? (y/n): ").strip().lower()
    if isCollaborators == "y":
        return True
    elif isCollaborators == "n":
        return False
    else:
        invalidAnswerExit()
        

def defaultCommit(args):
    path = args["path"]
    cmds = []
    handleGitInit(path)
    print("here?", path, f"git -C {path} init")
    isCommitNeeded = checkCommit(args["path"])
    if isCommitNeeded:
        cmds += [
        f"git -C {path} add ."
        ]
        commit_msg = input("commit message (double quotes are not allowed): ")
        if "\"" in commit_msg:
            print("double quotes detected, error!")
            sys.exit(15)
        cmds.append(f"git -C {path} commit -m \"{commit_msg}\"")
    for cmd in cmds:
        runCmd(cmd, stdout=PIPE, stderr=PIPE)

def getToken():
    path = tokenPath()["path"] # directory path
    file_= tokenPath()["file_"] # file path
    if os.path.exists(path + file_):
        try:
            with open(path+file_, "r") as f:
                token = f.read()
            if token != "":
                return token
        except FileNotFoundError as err:
            print("Error token file has been remove or modified in runtime")
            sys.exit(9)
    return None

def isTokenSaved(): # checks if the token is already saved or not
    path = tokenPath()["path"]
    file_= tokenPath()["file_"]
    if os.path.exists(path + file_):
        try:
            with open(path+file_, "r") as f:
                token = f.read()
            if token != "":
                return True
            return False
        except FileNotFoundError as err:
            return False
    else:
        return False

def saveTokenIfnotSaved(token):
    if not isTokenSaved():
        wantTosaveToken = input("Do you want to save your token (y/n): ").strip().lower()
        if wantTosaveToken == "y":
            saveToken(token)
        elif wantTosaveToken != "n":
            invalidAnswerExit()

def handleUsername(args): #self explanatory
    fpath = usernamePath()["path"]+usernamePath()["file_"]
    reg = re.compile("^([a-z0-9](?:-?[a-z0-9]){1,39})",re.IGNORECASE)
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
                data = f.read()
    else:
        data = None
    if "user" in args["new"] :
        username = getUserName()
        if username != reg.findall(username)[0]:
            print("Invalid username")
            sys.exit(8)
        saveUsername(username)
        return username
    elif data and data != "":
        print("Username saved as "+data)
        return data
    else:
        username = getUserName()
        if username != reg.findall(username)[0]:
            print("Invalid username")
            sys.exit(8)
        saveUsername(username)
        return username

def handleToken(args, username):
    if "token" in args["new"] :
        token = cacheToken(username)
        checkTokenValidation(token)
        saveToken(token)
        print("token got saved, you can either run this script with '-new token' argument again or go to "+tokenPath()["path"]+tokenPath()["file_"],"and edit the file.")
    elif not isTokenSaved():
        token = cacheToken(username)
        checkTokenValidation(token)
        saveTokenIfnotSaved(token)
    elif isTokenSaved():
        token = getToken()
    if token == None:
        print("error: token is None")
        sys.exit(3)
    return token

def handleGitInit(path):
    files_dirs = os.listdir(path)
    if ".git" not in files_dirs:
        runCmd(f"git -C {path} init", stdout=PIPE, stderr=PIPE)

def handleGitIgnore(path):
    files_dirs = os.listdir(path)
    files = input("Enter name of the file(s) you want to ignore seperated by commas if there one than one file: ").split(",")
    files = [x.strip() for x in files]
    if ".gitignore" not in files_dirs:
        with open(f"{path}{os.sep}.gitignore", "w") as f:
            f.write("\n".join(files))
            f.write("\n")
    elif ".gitignore" in files_dirs:
        with open(f"{path}{os.sep}.gitignore", "a") as f:
            f.write("\n".join(files))
            f.write("\n")
    handleGitInit(path)
    runCmd(f"git -C {path} add .gitignore", stdout=PIPE, stderr=PIPE)
    runCmd(f"git -C {path} rm -rf --cached .", stdout=PIPE, stderr=PIPE)

def handleRmGitIgnore(path):
    files_dirs = os.listdir(path)
    if ".gitignore" not in files_dirs:
        print("there is no '.gitignore' file...")
        sys.exit(15)
    files = [f.strip() for f in input("Enter name of the file(s) you want to keep track of seperated by commas if there one than one file: ").split(",")]
    with open(f"{path}{os.sep}.gitignore") as f:
        lines = f.readlines()
    lines = [re.sub("\n$","",line) for line in lines]
    files = [line for line in lines if line not in files]
    with open(f"{path}{os.sep}.gitignore", "w") as f:
        f.write("\n".join(files))
    handleGitInit(path)
    runCmd(f"git -C {path} add .gitignore", stdout=PIPE, stderr=PIPE)
    runCmd(f"git -C {path} rm -rf --cached .")



def handleCollaborators(**credentials):
    username = credentials["username"]
    token = credentials["token"]
    name = credentials["name"]
    try:
        n = int(input("how many collaborators do you want to invite: ")) # number of collaborattors
    except ValueError:
        print("Error! invalid number!")
        sys.exit(13)
    collaborators = []
    hotkey = "ctrl + c"
    for i in range(1,n+1):
        validName = True
        try:
            while True:
                if not validName:
                    print(collaborator,"is an invalid name, Please make sure that you've spelled it correctly!")
                print(f"({hotkey.upper()}) to skip, if that did not skip then press enter (return key).")
                collaborator = input("name of the collaborator number "+str(i)+" : ").strip()
                reg = re.findall("^([a-z0-9](?:-?[a-z0-9]){1,39})",collaborator,flags=re.IGNORECASE)
                if (not reg) or (collaborator != reg[0]):
                    validName = False
                elif collaborator == reg[0]:
                    validName = True
                    
                    collaborators.append(collaborator)
                if collaborator == "":
                    print("Error, please enter a valid name!")
                    sys.exit(14)
                if validName:
                    break
        except KeyboardInterrupt:
            print("Skipped!")
            break
        
    if collaborators:
        print(""" permission types:
    * pull - can pull, but not push to or administer this repository.
    * push - can pull and push, but not administer this repository.
    * admin - can pull, push and administer this repository.
    * maintain - Recommended for project managers who need to manage the repository without access to sensitive or destructive actions.
    * triage - Recommended for contributors who need to proactively manage issues and pull requests without write access.
    Default: push (just press enter)
    """)
    for collaborator in collaborators:
        permission = input("permission for '"+collaborator+"' : ")
        permissions = ["pull", "push", "admin", "maintain", "triage"]
        if permission not in permissions:
            permission = "push"
        command = "curl -H 'Authorization: token "+token+"' 'https://api.github.com/repos/"+username+"/"+name+"/collaborators/"+collaborator+"' -X PUT -d '{\"permission\":\""+permission+"\"}'"
        process = openBash(command, returncode=True,stderr=PIPE, stdout=PIPE, error="error!\nperhaps you misspelled collaborator name, your access token, repository name or your username...")
        returncode = process["returncode"]
        out = process["out"]
        err = process["err"]
        out = json.loads(out)
        if "message" in out:
            print(out["message"])
        else:
            print("Added!")

def changeVisibility(**credentials):
    username = credentials["username"]
    token = credentials["token"]
    name = credentials["name"]
    # visiblity = promptPyInquirer({
    #     "name": "visibility",
    #     "question": "change it to?",
    #     "choices": ["private", "public"]
    # })["visibility"]
    if(getOS() == "windows"):
        visiblity = promptPyInquirer({
            "type": "list",
            "name": "visibility",
            "message": "change it to?",
            "choices": ["private", "public"]
        })["visibility"]
    else:
        visiblity = listPromptInquirer({
            "name": "visibility",
            "question": "change it to?",
            "choices": ["private", "public"]
        })
    command = "curl -H 'Authorization: token "+token+"' 'https://api.github.com/repos/"+username+"/"+name+"' -H 'Accept: application/vnd.github.nebula-preview+json' -X PATCH -d '{\"visibility\":\""+visiblity+"\"}'"
    
    loading = Loading(type="dynamic", startText="Changing", stopText="Changed!")
    loading.start()
    process = openBash(command, stderr=PIPE, stdout=PIPE, returncode=True)
    if("Visibility is already " in process["out"]):
        loading.abort()
        print("Visibility is already private.")
    elif "Not found" in process["err"]:
        print("Not found.")
        sys.exit(12)
    elif process["returncode"] == 0: 
        loading.stop()

def createResourceDir():
    path = tokenPath()["path"]
    if not os.path.exists(path=path):
        os.makedirs(path)
def tokenPath(): # get token path depending on the operating system
    if getOS() == "windows":
        return {"path":"C:\\.gd\\","file_":".gd-token"}

def usernamePath(): #get username path depending on the operating system
    if getOS() == "windows":
        return {"path":"C:\\.gd\\","file_":".gd-username"}


def saveToken(token):
    path = tokenPath()["path"]
    file_= tokenPath()["file_"]
    with open( path + file_, "w" ) as ft:
        ft.write(token)

def saveUsername(username):
    fpath = usernamePath()["path"]+usernamePath()["file_"]
    with open(fpath, "w") as f:
        f.write(username)

def getUserName():
    return input("username (on github): ")

def getRepoName(repo):
    repo = repo if repo else input("Enter the name of the repository: ")
    return checkRepositoryName(repo)
    

def getGithubUrl(data):
    # data['name'] = data['name'].replace(" ","-")
    return f"https://github.com/{data['username']}/{data['name']}.git"


def infoAboutToken():
    print("If you don't have your token yet go get it from https://github.com/settings/tokens (you must be loggedIn)")

def infoAboutRepo(username,token,repo,collaboratorsCmdExist, path):
    name = getRepoName(repo)
    if not createRepository( getGithubUrl({"name":name, "username":username}), token, path):
        return {"name":name, "username":username}
    
    private = input("want it to be private? (y/n): ").lower()
    if private == "y":
        private = True
    elif private == "n":
        private = False
    else:
        invalidAnswerExit()
    if collaboratorsCmdExist:
        collaborators = True
    elif not collaboratorsCmdExist:
        collaborators = promptCollaborators()
    return {"name": name,"private":private,"username":username, "collaborators":collaborators}

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

def openBrowser(url):
    print("[¤] press any key to open repository in your browser or q to quit the program.")
    if keyboard.read_key() == "q":
        sys.exit(0)
    else:
        load = Loading(startText="Opening",stopText="Opened!", timeout=0.18)
        load.start()
        webbrowser.open(url)
        load.stop()

def createRepository(url, token, path): #check if we should create a repository, if not then it returns True
    protocolAndSlash = "https://"
    suburl = url[len(protocolAndSlash):]
    username = re.findall("^https://github.com/(\w*)",url)[0]
    url = protocolAndSlash+username+":"+token+"@"+suburl
    processing = Loading(stopText="", type="dynamic", timeout=.13)
    processing.start()
    process = openBash('git ls-remote '+url, stderr=PIPE, stdout=PIPE, returncode=True, timeout=10)
    processing.stop()
    returncode = process["returncode"]
    err = process["err"]
    if 'remote: Invalid username or password.\nfatal: Authentication failed' == err:
        print(err)
        sys.exit(3)
    if returncode != 0 and err == "":
        return False
    if returncode == 0:
        return False
    elif returncode != 0 and "Repository not found" in err:
        return True
    else:
        print("ERROR")
        sys.exit(returncode)

def addRemoteAndPush(url, path, remote_name="origin"):
    out = runCmd("git -C "+ path +" remote", stdout=PIPE, stderr=PIPE)
    if remote_name in out:
        runCmd(f"git -C {path} remote rm {remote_name}")
    load = Loading(startText="pushing to github")
    load.start()
    runCmd(f"git -C {path} remote add {remote_name} {url}", stdout=PIPE, stderr=PIPE)
    runCmd(f"git -C {path} push -u {remote_name} main")
    load.stop()
    openBrowser(url)

def invalidAnswerExit():
    print("invalid answer")
    sys.exit(12)

def repoNotFoundError():
    print("ERROR\nRepository doesn't exist, check your repository name!")
    sys.exit(3)


def checkTokenValidation(token):
    load = Loading(startText="Checking Token Access Validation", stopText="")
    load.start()
    if re.search("[^\w]",token) or token == "":
        load.abort()
        print("Invalid token")
        sys.exit(17)
    openBash(f"curl -f -H \"Authorization: token {token}\" https://api.github.com/users/codertocat -I", stdout=PIPE, stderr=PIPE, error="there is no such token available",load=load, printBashError=False,timeout=10)
    load.stop()
    pass

def checkRepositoryName(name):
    regex = re.compile("[^A-Za-z0-9_\-]{1,}")
    maxChar = 100
    name = name[:maxChar]
    
    if regex.search(name):
        newName = regex.sub("-", name)
        printWarning("Your new repository will be created as:",newName,sep="\n\t",flush=True)
        confirm = input("Do you want to Try another one? (y/n): ").strip().lower()
        if confirm == "y":
            confirm = False
        elif confirm == "n":
            confirm = True
        else:
            invalidAnswerExit()
        if not confirm:
            name = checkRepositoryName(input("Try another repository name: "))
        elif confirm:
            name = newName
    return name

def checkSoftware(name, cmd, url=None):
    err = f"It seems that {name} is not in your machine, please make sure to download it first"
    err += f"\n you can find it at {url}" if url else ""
    runCmd(cmd, stdout=DEVNULL,
        error= err
    )

def checkCommit(path):
    out = runCmd(f"git -C {path} status", stdout=PIPE, stderr=PIPE)
    if "nothing to commit, working tree clean" in out:
        print(out)
        return False
    return True

def masterToMain(path):
    out = runCmd(f"git -C {path} branch", stdout=PIPE, stderr=PIPE)
    if "main" in out:
        return
    runCmd(f"git -C {path} branch -m master main", stdout=PIPE, stderr=PIPE)
    runCmd(f"git -C {path} checkout main", stdout=DEVNULL, stderr=PIPE)


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

if __name__ == "__main__":
    main()