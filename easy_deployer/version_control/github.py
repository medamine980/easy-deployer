import click
import os
import sys
import re
import json
import time

from subprocess import PIPE, DEVNULL

from easy_deployer.utilities import ERROR_CODES
from easy_deployer.utilities.terminal import check_software, handle_git_init, default_git_commit, run_cmd\
    ,open_bash
from easy_deployer.utilities.process import Loading, get_os, open_browser
from easy_deployer.utilities.interface import path_input, text_input, confirm_input, select_input,\
    print_color, print_warning

available_commands = ('create-update', 'update', 'delete', 'clone')

@click.command(
        help="""You basically enter one of the following commands:\n
        ¤ create-update (which is the default one)\n
        ¤ update (to update an existing repository)\n
        ¤ delete (to delete an existing repository)\n
        ¤ clone (to clone a repository)
then you need to specify the path by using the -p or --path argument."""
)
@click.option("-cmd", "--command",
              type=click.Choice(available_commands,case_sensitive=True),
              help="commands, default command is 'create-update'")
@click.option("-p", "--path", type=str, help="Path of the folder")
@click.option("-new", multiple=True, type=click.Choice(('user', 'token'), case_sensitive=False), 
              help="if you want to resave user or token")
@click.option("-repo", "--repository", "name", type=str, help="Repository name")
@click.option("-ac", "--add-collaborators", "add_collab", is_flag=True, help="If you want to add collaborators, repository must exist to do so else you'll get an error")
@click.option("-visibility", is_flag=True, help="Change visibility")
@click.option("-git-ig", "--git-ignore", is_flag=True, help="Add a file to the .gitignore file")
@click.option("-rm-git-ig", "--rm-git-ignore", is_flag=True, help="Remove file from .gitignore")
@click.pass_context
def main(ctx, command, path, new, name, add_collab, visibility, git_ignore, rm_git_ignore):
    if get_os() == "windows": # to clean the screen
        os.system("cls") # clears the console
    path, command = handle_args(path, command, git_ignore=git_ignore, rm_git_ignore=rm_git_ignore)
    check_software("git", "git --help") # check if git is installed in the current machine
    create_resource_dir() #create resources
    # Update command is invoked
    if command == "update": # check if -u or --update is present when the user runs the script
        return update(path=path, name=name, add_collab=add_collab, new=new, visibility=visibility)
    elif command == "delete":
        return delete(path=path, name=name, new=new)
    elif command == "create-update":
        return create_update(path=path, name=name, new=new, add_collab=add_collab, visibility=visibility)
    elif command == "clone":
        return clone(path)

# Functions responsable for commands
def create_update(path, name, new, add_collab, visibility):
    """This functions runs when the user chooses the 'create-update' command"""
    info_about_token() # info telling the user that he needs a token to create a repository
    default_git_commit(path) # git add, git commit etc...
    username = handle_username(new) # takes care of the username 
    token = handle_token(new, username) # takes care of the access token
    data = info_about_repo(username, token, name, add_collab, path)
    url = get_github_URL(data)
    create_repo = repository_creation_needed(url, token, path)
    if create_repo:
        loading = Loading(start_text="Creating repository", stop_text="repository has been created!", type="dynamic", timeout=.1)
        isCollaborators = data["collaborators"]
        data = {k:v for k,v in data.items() if k != "username" and k != "collaborators"}
        # cmd down is a command for creating a repository 
        loading.start()
        cmd = 'curl -f -u '+username+':'+token+' https://api.github.com/user/repos -d "'+json.dumps(data).replace("\"","\\\"")+'"'
        out = open_bash(cmd, stderr=PIPE ,stdout=PIPE, loading=loading, error="""Error has been caught:
            Authorization Required! check your username and password
        """, print_bash_error=False)
        loading.stop()
        save_token_if_not_saved(token)
        if isCollaborators:
            handle_collaborators(username=username, token=token, repo_name=data["name"])
    elif not create_repo:
        #if we don't need to create a repository (which means it's already available) then we simply print that below
        print("repository already exist...")
        if(visibility):
            if visibility:
                changeVisibility(username=username, token=token, repo_name=data["name"])
        if(add_collab):
            handle_collaborators(username=username, token=token, repo_name=data["name"])
    master_to_main(path)
    add_remote_and_push(url, path, username=username, token=token, repo_name=data["name"])

def update(path, name, new, visibility, add_collab):
    """
    it gets called when "-u" or "--update" are available
    it updates or (pushs) the specified directory to the specified repository
    """
    default_git_commit(path)
    username = handle_username(new)
    token = handle_token(new, username)
    repo_name = get_repo_name(name, path)
    url = get_github_URL({"username":username,"name":repo_name})
    if add_collab:
        add_collaborators(path, name, new, username=username, token=token, name=repo_name)
    if visibility:
        changeVisibility(username=username, token=token, repo_name=repo_name)
    create_repo = repository_creation_needed(url,token, path)
    save_token_if_not_saved(token)
    if create_repo:
        repo_not_found()
    elif not create_repo:
        master_to_main(path)
        add_remote_and_push(url, path, username=username, token=token, repo_name=repo_name)

def delete(path, name, new):
    username = handle_username(new)
    token = handle_token(new, username)
    repo_name = get_repo_name(name, path)
    url = get_github_URL({ "username":username, "name":repo_name })
    create_repo = repository_creation_needed(url=url,token=token, path=path)
    if create_repo:
        repo_not_found()
    elif not create_repo:
        loading = Loading(start_text="Deleting Repository",stop_text="Repository Deleted", type="dynamic", timeout=.1)
        loading.start()
        open_bash(f"curl -X DELETE -H 'Authorization: token {token}' https://api.github.com/repos/{username}/{repo_name}", stdout=PIPE, stderr=PIPE ,loading=loading)
        loading.stop()

def clone(path:str):
    github_url = text_input(f"Entrer the github url you wish to clone to ({path}):", default="https://github.com")
    run_cmd(f"git clone {github_url} {path}")

# Handlers
def handle_args(path: str, command: str, git_ignore, rm_git_ignore):
    if command is None:
        command = select_input("Which command would you like to execute:", 
                               choices=('create-update', 'update', 'delete'), 
                               default="create-update")
    if command not in ("delete", "clone") or git_ignore or rm_git_ignore:
        if path is None:
            path = path_input("Enter path of the folder: ",  only_directories=True, default=os.getcwd(),
                            validate=lambda x: os.path.isdir(x), invalid_message="Invalid directory path!")
        elif not os.path.isdir(path):
            print("Invalid path")
            sys.exit(ERROR_CODES["invalid_path"])
        if git_ignore:
            handle_git_ignore(path)
        if rm_git_ignore:
            handle_rm_git_ignore(path)
        return os.path.abspath(path.strip()), command
    return None, command

def handle_git_ignore(path):
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
    handle_git_init(path)
    run_cmd(f"git -C {path} add .gitignore", stdout=PIPE, stderr=PIPE)
    run_cmd(f"git -C {path} rm -rf --cached .", stdout=PIPE, stderr=PIPE)

def handle_rm_git_ignore(path):
    files_dirs = os.listdir(path)
    if ".gitignore" not in files_dirs:
        print("there is no '.gitignore' file...")
        sys.exit(ERROR_CODES["missing_gitignore_file"])
    files = [f.strip() for f in input("Enter name of the file(s) you want to keep track of seperated by commas if there one than one file: ").split(",")]
    with open(f"{path}{os.sep}.gitignore") as f:
        lines = f.readlines()
    lines = [re.sub("\n$","",line) for line in lines]
    files = [line for line in lines if line not in files]
    with open(f"{path}{os.sep}.gitignore", "w") as f:
        f.write("\n".join(files))
    handle_git_init(path)
    run_cmd(f"git -C {path} add .gitignore", stdout=PIPE, stderr=PIPE)
    run_cmd(f"git -C {path} rm -rf --cached .")

def handle_username(new): #self explanatory
    fpath = username_path()["path"]+username_path()["file_"]
    reg = re.compile("^([a-z0-9](?:-?[a-z0-9]){1,39})",re.IGNORECASE)
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
                data = f.read()
    else:
        data = None
    if "user" in new :
        username = get_username()
        if username != reg.findall(username)[0]:
            print("Invalid username")
            sys.exit(8)
        save_username(username)
        return username
    elif data and data != "":
        print("Username saved as "+data)
        return data
    else:
        username = get_username()
        if username != reg.findall(username)[0]:
            print("Invalid username")
            sys.exit(8)
        save_username(username)
        return username

def handle_token(new, username):
    if "token" in new :
        token = cache_token(username)
        checkTokenValidation(token)
        save_token(token)
        print("token got saved, you can either run this script with '-new token' argument again or go to "+token_path()["path"]+token_path()["file_"],"and edit the file.")
    elif not isTokenSaved():
        token = cache_token(username)
        checkTokenValidation(token)
        save_token_if_not_saved(token)
    elif isTokenSaved():
        token = getToken()
    if token is None:
        print("error: token is None")
        sys.exit(ERROR_CODES["token_is_none"])
    return token

def handle_collaborators(**credentials):
    username = credentials["username"]
    token = credentials["token"]
    name = credentials["repo_name"]
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
        process = open_bash(command, returncode=True,stderr=PIPE, stdout=PIPE, error="error!\nperhaps you misspelled collaborator name, your access token, repository name or your username...")
        returncode = process["returncode"]
        out = process["out"]
        err = process["err"]
        out = json.loads(out)
        if "message" in out:
            print(out["message"])
        else:
            print("Added!")


#ADDERS
def add_collaborators(path, name, new, username=None, token=None, repo=None):
    username = username if username else handle_username(new)
    token = token if token else handle_token(new, username)
    repo = repo if repo else get_repo_name(name, path)
    url = get_github_URL({"username": username, "name":repo})
    repositoryNeeded = repository_creation_needed(url, token, path)
    if repositoryNeeded:
        print("ERROR\nRepository doesn't exist, check your repository name!")
        sys.exit(3)
    handle_collaborators(username=username, token=token, name=repo)

def add_remote_and_push(url, path, repo_name, username, token, remote_name="origin",):
    out = run_cmd("git -C "+ path +" remote", stdout=PIPE, stderr=PIPE)
    if remote_name in out:
        run_cmd(f"git -C {path} remote rm {remote_name}")
    loading = Loading(start_text="pushing to github")
    loading.start()
    run_cmd(f"git -C {path} remote add {remote_name} {url}", stdout=PIPE, stderr=PIPE)
    process = run_cmd(f"git -C {path} push -u {remote_name} main --dry-run", quit_on_error=False,
                      returncode=True, stderr=PIPE)
    run_cmd(f"git -C {path} push -u {remote_name} main")
    if "err" in process and "returncode" in process and process["returncode"] != 0: 
        if "hint: (e.g., 'git pull ...') before pushing again." in process["err"]:
            loading.abort()
            print_color("\n" + process["err"], fg="yellow")            
            OPTION_1 = """Clone the repository, then just copy its .git folder to here, and therefore you will lose your current commits but not the past one's (from the cloned repo)"""
            OPTION_2 = "Exit"
            options = select_input("There is couple options to fixed it", choices=[OPTION_1, OPTION_2])
            if options == OPTION_1:
                temp_dir = "../temp" + str(int(time.time()))
                open_bash(f"git clone https://{token}@github.com/{username}/{repo_name}.git {temp_dir}")
                open_bash(f"""
                          shopt -s extglob
                          cp -r !(.git) "{temp_dir}"
                          cp -r {temp_dir}/.git .
                          rm -r {temp_dir}
                          """)
                commit_again = confirm_input("A git commit is about to happen, are you ok with that")
                if commit_again:
                    default_git_commit(path)
                return add_remote_and_push(url, path, repo_name, username, token)
            elif options == OPTION_2:
                print_color("Exit", fg="green")
                sys.exit(0)
        else:
            sys.exit(process["returncode"])
    loading.stop()
    open_browser(url)       

#CHECKERS
def check_repository_name(repo_name):
    regex = re.compile("[^A-Za-z0-9_\-]{1,}")
    max_char = 100
    repo_name = repo_name[:max_char]
    
    if regex.search(repo_name):
        new_name = regex.sub("-", repo_name)
        print_warning("Your new repository will be created as:",new_name,sep="\n\t",flush=True)
        confirm = confirm_input("Do you want to Try another one?: ", default=True)
        if not confirm:
            repo_name = check_repository_name(text_input("Try another repository name: "))
        elif confirm:
            repo_name = new_name
    return repo_name

def checkTokenValidation(token):
    loading = Loading(start_text="Checking Token Access Validation", stop_text="")
    loading.start()
    if re.search("[^\w]",token) or token == "":
        loading.abort()
        print("Invalid token")
        sys.exit(17)
    open_bash(f"curl -f -H \"Authorization: token {token}\" https://api.github.com/users/codertocat -I", stdout=PIPE, stderr=PIPE, error="there is no such token available",loading=loading, print_bash_error=False,timeout=10)
    loading.stop()
    pass


# RESOURCES
def create_resource_dir():
    path = token_path()["path"]
    if not os.path.exists(path=path):
        os.makedirs(path)

# PATHS
def token_path(): # get token path depending on the operating system
    if get_os() == "windows":
        return {"path":"C:\\.gd\\","file_":".gd-token"}

def username_path(): #get username path depending on the operating system
    if get_os() == "windows":
        return {"path":"C:\\.gd\\","file_":".gd-username"}
    
# GETTERS
def get_username():
    return text_input("username (on github): ")

def getToken():
    path = token_path()["path"] # directory path
    file_= token_path()["file_"] # file path
    if os.path.exists(path + file_):
        try:
            with open(path+file_, "r") as f:
                token = f.read()
            if token != "":
                return token
        except FileNotFoundError as err:
            print("Error token file has been remove or modified in runtime")
            sys.exit(ERROR_CODES["token_file_not_found"])
    return None

def get_repo_name(repo, path):
    if not repo:
        out = run_cmd(f"git -C {path} remote -v", stdout=PIPE, stderr=PIPE, quit_on_error=False)
        if out:
            regex = re.compile("https:\/\/github\.com\/.+/(.+)\.git")
            matchs = regex.findall(out)
            if matchs:
                repo = text_input(
                    message="Enter the name of the repository:",
                    default=matchs[1]
                    )
            else:
                repo = text_input("Enter the name of the repository: ")
        else:
            repo = text_input("Enter the name of the repository: ")
    
    return check_repository_name(repo)

def get_github_URL(data):
    # data['name'] = data['name'].replace(" ","-")
    return f"https://github.com/{data['username']}/{data['name']}.git"

#INFO
def info_about_token():
    print("If you don't have your token yet go get it from https://github.com/settings/tokens (you must be loggedIn)")

def info_about_repo(username,token,repo,collaboratorsCmdExist, path):
    repo_name = get_repo_name(repo, path)
    if not repository_creation_needed( get_github_URL({"name":repo_name, "username":username}), token, path):
        return {"name":repo_name, "username":username}
    
    private = confirm_input("Want it to be private: ")
    if collaboratorsCmdExist:
        collaborators = True
    elif not collaboratorsCmdExist:
        collaborators = prompt_collaborators()
    return {"name": repo_name,"private":private,"username":username, "collaborators":collaborators}


# SAVERS
def save_username(username):
    fpath = username_path()["path"]+username_path()["file_"]
    with open(fpath, "w") as f:
        f.write(username)

def save_token_if_not_saved(token):
    if not isTokenSaved():
        wantTosaveToken = confirm_input("Do you want to save your token (y/n): ")
        if wantTosaveToken:
            save_token(token)

def save_token(token):
    path = token_path()["path"]
    file_= token_path()["file_"]
    with open( path + file_, "w" ) as ft:
        ft.write(token)

def cache_token(username):
    path_token = path_input(
        message="Enter either path of the file that contains the access token, or enter the access toke directly:",
        invalid_message="Invalid path",
        validate=lambda x: os.path.isfile(x) if re.search("[/\/]") else len(x) > 0
    )
    if os.path.isfile(path_token):
        with open(path_token, 'r') as f:
            return f.read()
    else:
        return path_token
    
#is Functions (return bool)

def isTokenSaved() -> bool: # checks if the token is already saved or not
    path = token_path()["path"]
    file_= token_path()["file_"]
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

#REPO STUFF
def repository_creation_needed(url, token, path): #check if we should create a repository, if not then it returns True
    protocolAndSlash = "https://"
    suburl = url[len(protocolAndSlash):]
    username = re.findall("^https://github.com/(\w*)",url)[0]
    url = protocolAndSlash+username+":"+token+"@"+suburl
    processing = Loading(stop_text="", type="dynamic", timeout=.13)
    processing.start()
    process = open_bash('git ls-remote '+url, stderr=PIPE, stdout=PIPE, returncode=True, timeout=10)
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

def master_to_main(path):
    out = run_cmd(f"git -C {path} branch", stdout=PIPE, stderr=PIPE)
    if "main" in out:
        return
    run_cmd(f"git -C {path} branch -m master main", stdout=PIPE, stderr=PIPE)
    run_cmd(f"git -C {path} checkout main", stdout=DEVNULL, stderr=PIPE)

def prompt_collaborators():
    isCollaborators = confirm_input("do you want collaborators with you in this repository: ")
    return isCollaborators

def changeVisibility(username, token, repo_name):
    visiblity = select_input(
        "Change it to:",
        choices=["private", "public"]
    )
    command = "curl -H 'Authorization: token "+token+"' 'https://api.github.com/repos/"+username+"/"+repo_name+"' -H 'Accept: application/vnd.github.nebula-preview+json' -X PATCH -d '{\"visibility\":\""+visiblity+"\"}'"
    
    loading = Loading(type="dynamic", start_text="Changing", stop_text="Changed!")
    loading.start()
    process = open_bash(command, stderr=PIPE, stdout=PIPE, returncode=True)
    if("Visibility is already " in process["out"]):
        loading.abort()
        print("Visibility is already private.")
    elif "Not found" in process["err"]:
        print("Not found.")
        sys.exit(12)
    elif process["returncode"] == 0: 
        loading.stop()

def repo_not_found():
    print("ERROR\nRepository doesn't exist, check your repository name!")
    sys.exit(ERROR_CODES["repository_not_found"])