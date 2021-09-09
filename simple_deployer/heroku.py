import os, sys, keyboard, json, re
from subprocess import Popen, PIPE, run, DEVNULL
from argparse import ArgumentParser

from shared_functions import Loading, runCmd

def main():
    args = takeArgs()
    checkSoftware("git", "git --help")
    checkSoftware("heroku", "heroku --help", "https://devcenter.heroku.com/articles/heroku-cli#download-and-install")
    args["path"] = os.path.abspath(args["path"])
    os.chdir(args["path"]) #changing to path
    print("Directory changed to "+os.getcwd()) #informing the user that the directory has changed
    if args["cmd"] == "update":
        update()
        return
    elif args["cmd"] == "delete":
        delete()
    elif args["cmd"] == "logs":
        herokuLogs()
    elif args["cmd"] == "create-update":
        if args["framework"] == "flask":
            __Flask__(args["path"])
        elif args["framework"] == "nodejs":
            __Nodejs__(args["path"])
        defaultCommit(args)
        masterToMain()
        if not herokuIsLoggedIn():
            herokuLogin()
        herokuAppExistence()
        herokuRemote()
        herokuPush()
        print("Done!")
        herokuOpen()

def update():
    isCommitNeeded = checkCommit()
    cmds = [
        "git add .",
    ]
    if isCommitNeeded:
        commit_msg = input("commit message: ")
        cmds.append(f"git commit -m \"{commit_msg}\"")
    else:
        print("Everything up-to-date")
        herokuOpen()
        sys.exit(0)
    for cmd in cmds:
        runCmd(cmd)
    if not herokuIsLoggedIn():
        herokuLogin()
    masterToMain()
    herokuRemote()
    herokuPush()
    herokuOpen()

def delete():
    if not herokuIsLoggedIn():
        herokuLogin()
    runCmd("heroku apps:destroy")
    sys.exit(0)

def takeArgs():
    parser = ArgumentParser(prog="heroku-deployer",
    usage="""You basically enter one of the following commands:
        ¤ create-update (which is the default one)
        ¤ update (to update an existing heroku-website)
        ¤ delete (to delete an existing heroku-website)
        ¤ logs (to log if there were any errors)
    then you need to specify the path by using the -p or --path argument.
    then you need to specify the language or framework you're using. e.g: nodejs flask etc...""",
         description="%(prog)s <commands> [options]")
    parser.add_argument("cmd", nargs="?", choices=["create-update", "update", "delete", "logs"], help="", default="create-update")
    parser.add_argument("-p", "--path", help="path of the folder you want to deploy.", required=True)
    parser.add_argument("-lang", "--language", dest="framework", default="flask", choices=["flask","nodejs"], help="language or the framework you're using.")
    return vars(parser.parse_args())

def defaultCommit(args):
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
        cmds.append(f"git commit -m \"{commit_msg}\"")
    for cmd in cmds:
        runCmd(cmd, stdout=PIPE, stderr=PIPE)

def herokuLogin():
    runCmd("heroku login -i", error="You have not been authenticated to heroku!")

def herokuIsLoggedIn():
    process = Popen("heroku whoami", shell=True, stdout=PIPE, stderr=PIPE)
    output = [i.decode() for i in process.communicate()][0]
    process.wait()
    if process.returncode == 0:
        print(f"Logged in as {output}")
        return True
    return False

def herokuAppExistence():
    isCreated = input("Have you created the app yet (y/n): ").lower()
    if isCreated == "n":
        appName = input("What do you want to name your app: ")
        runCmd(f"heroku create {appName}")
    elif isCreated == "y":
        pass
    else:
        print("Invalid answer!")
        sys.exit(3)

def herokuOpen():
    print("Do you want to open the app now? press any key to open it or q to exit the script: ")
    if keyboard.read_key() == "q":
        sys.exit(0)
    opening = Loading(startText="Opening", stopText="Opened")
    opening.start()
    runCmd("heroku open", load=opening)
    opening.stop()
        

def herokuRemote():
    hasRemote = runCmd("git remote -v", stdout=PIPE, stderr=PIPE)
    if not hasRemote:
        appName = input("App name: ")
        runCmd(f"heroku git:remote -a ${appName}")

def herokuPush():
    runCmd("git push heroku main")

def herokuLogs():
    runCmd("heroku logs")

def checkModule(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False

def handleGitInit(path):
    files_dirs = os.listdir(path)
    if ".git" not in files_dirs:
        runCmd("git init")

def checkSoftware(name, cmd, url=""):
    err = f"It seems that {name} is not in your machine, please make sure to download it first"
    err += f"\n you can find it at {url}" if url else ""
    runCmd(cmd, stdout=DEVNULL,
        error= err
    )



def masterToMain():
    out = runCmd("git branch", stdout=PIPE, stderr=PIPE)
    if "main" in out:
        return
    runCmd("git branch -m master main", stdout=PIPE, stderr=PIPE)
    runCmd("git checkout main", stdout=DEVNULL, stderr=PIPE)

def checkCommit():
    out = runCmd("git status", stdout=PIPE, stderr=PIPE)
    if "nothing to commit, working tree clean" in out:
        print(out)
        return False
    return True

class __Flask__():
    def __init__(self, path):
        self.path = path
        if self.checkFiles() is None:
            sys.exit(1)

    def checkFiles(self):
        files = [file.lower() for file in os.listdir(self.path)]
        required = ["runtime.txt", "requirements.txt", "Procfile"]
        for require in required:
            if require.lower() not in files:
                stop = self.missingFile(require)
                if stop:
                    print("script has been stopped, needs", require)
                    return None
        return True

    def missingFile(self, fileName):
        if fileName == "requirements.txt":
            print("requirements.txt is missing in your directory.\nplease run in your commandline/terminal type:'py freeze > requirements.txt'")
            return True
        if fileName == "runtime.txt":
            version = self._getRunTime()
            self.writeFile(fileName, "python-"+version)
        elif fileName == "Procfile":
            app = self._getProcfile()
            self.writeFile(fileName, f"web: gunicorn {app}:app")
        return False
            
    def _getRunTime(self):
        prompt = """
        Choose a python version:
        1. 3.9.4
        2. 3.8.9
        3. 3.7.10
        4. 3.6.13
        """
        print(prompt)
        choice = input("=> ")
        options = {
            "1": "3.9.4",
            "2": "3.8.9",
            "3": "3.7.10",
            "4": "3.6.13"
        }
        return options[choice]

    def _getProcfile():
        fileName = input("What is your main file name: ")
        return fileName.rsplit(".")[0]

    def writeFile(fileName, content):
        with open(fileName, "w") as f:
            f.write(content)

class __Nodejs__():
    def __init__(self,path):
        self.path = path
        checkSoftware("nodejs", "node -v")
        self.checkFiles()

    def checkFiles(self):
        files = [file for file in os.listdir(self.path)]
        required = ["package.json", ".gitignore"]
        for r in required:
            if r not in files:
                self.missingFile(r)
        
        self.npmStart(self.path+os.sep+"package.json")
        self.gitignoreNodeModules(self.path+os.sep+".gitignore")

    def missingFile(self, filename):
        if filename == "package.json":
            print("Creating package.json")
            runCmd("npm init -y")
        elif filename == ".gitignore":
            f = open(self.path+os.sep+".gitignore", "w")
            f.close()

    def gitignoreNodeModules(self, gitignorePath):
        with open(gitignorePath) as f:
            string = f.read()
            if re.search("^(/node_modules|node_modules/|[\\\]node_modules|node_modules[\\\])", string):
                string = string + "/node_modules" if string[-1] == "\n" else string + "\n/node_modules"
        with open(gitignorePath, "w") as f:
            f.write(string)



    def npmStart(self, packagePath):
        with open(packagePath) as f:
            # print(f.read())
            packageDict = json.load(f)
            if "engines" not in packageDict:
                packageDict["engines"] = {}
            if "node" not in packageDict["engines"]:
                nodeVersion = re.findall("^v(\d+)",runCmd("node -v", stdout=PIPE, stderr=PIPE))
                packageDict["engines"]["node"] = nodeVersion[0] if len(nodeVersion) > 0 else ""
            if "scripts" not in packageDict:
                packageDict["scripts"] = {}
                self.mainFile = input("Main file name that's gonna run: ")
                packageDict["scripts"]["start"] = "node "+self.mainFile
            elif "scripts" in packageDict and type(packageDict["scripts"] is dict):
                if not "start" in packageDict["scripts"]:
                    self.mainFile = input("Main file name that's gonna run: ")
                    packageDict["scripts"]["start"] = "node "+self.mainFile

        with open(packagePath, "w") as f:
            f.write(json.dumps(packageDict, indent=4))
        
                
