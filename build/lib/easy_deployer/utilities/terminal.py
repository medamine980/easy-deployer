import sys
import os

from subprocess import Popen, PIPE, DEVNULL

from easy_deployer.utilities.process import Loading, get_os
from easy_deployer.utilities import ERROR_CODES

def check_software(name, cmd, url=None):
    err = f"It seems that {name} is not in your machine, please make sure to download it first"
    err += f"\n you can find it at {url}" if url else ""
    run_cmd(cmd, stdout=DEVNULL,
        error= err
    )

def run_cmd(
        cmd, 
        stdin=None, 
        stdout=None, 
        stderr=None, 
        error: str = "an error has been caught\n",
        error_code: int = 10,
        returncode: bool = False,
        quit_on_error: bool = True,
        timeout: float = None,
        loading: Loading = None
        ):
    """
    * cmd (string): the command to be executed
    * options(dict):
            * stdin (None|PIPE)
            * stdout (None|PIPE)
            * error (str)
            * error_code (int)
            * quit_on_error (bool)
            * timeout (None|float)
            * loading (Loading)  
    """
    process = Popen(cmd, shell=True, stdin=stdin, stderr=stderr, stdout=stdout)
    out, err = process.communicate()
    if timeout:
        process.wait(timeout=timeout)
    elif not timeout:
        process.wait()
    if returncode:
        out = out.decode() if out != None else out
        err = err.decode() if err != None else err
        return {"returncode":process.returncode,"out":out, "err":err}
    if process.returncode != 0 and quit_on_error:
        if loading:
            loading.abort()
        print(error)
        print(err.decode()) if err else ""
        if error_code is None:
            error_code = process.returncode
        sys.exit(error_code)
    return out.decode() if out != None else None

def open_bash(input_, stdin=PIPE, stdout=None, stderr=None, error="an error has been caught\n",
              returncode=False, print_bash_error=True, loading: Loading=None, timeout=None):
    os_ = get_os()
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
            sys.exit(ERROR_CODES["command_not_found"])
        if returncode:
            out = out.decode() if out != None else out
            err = err.decode() if err != None else err
            return {"returncode":process.returncode,"out":out, "err":err}
        if process.returncode != 0:
            if loading:
                loading.abort()
            if print_bash_error:
                print(error+"\n",err.decode() if err else "",sep="")
            else:
                print(error)
            sys.exit(5)
        return out.decode() if out else out

def default_git_commit(path):
    """This function handles default commits, (git add ., git commit -m "message")"""
    # os.chdir(path)
    cmds = []
    handle_git_init(path)
    is_commit_needed = check_commit(path)
    if is_commit_needed:
        cmds += [
        f"git -C {path} add ."
        ]
        commit_msg = input("commit message (double quotes are not allowed): ")
        if "\"" in commit_msg:
            print("double quotes detected, error!")
            sys.exit(ERROR_CODES["double_quotes_not_allowed"])
        cmds.append(f"git -C {path} commit -m \"{commit_msg}\"")
        for cmd in cmds:
            start_text="processing"
            if cmds.index(cmd) == 0:
                # command is "git add ."
                start_text="Adding files"
            elif cmds.index(cmd) == 1:
                # command is git commit
                start_text="Committing changes"
            loading = Loading(start_text=start_text, stop_text="", timeout=1)
            loading.start()
            run_cmd(cmd, stdout=PIPE, stderr=PIPE, loading=loading)
            loading.stop()

def handle_git_init(path):
    files_dirs = os.listdir(path)
    if ".git" not in files_dirs:
        run_cmd(f"git -C {path} init", stdout=PIPE, stderr=PIPE)

def check_commit(path):
    out = run_cmd(f"git -C {path} status", stdout=PIPE, stderr=PIPE)
    if "nothing to commit, working tree clean" in out:
        print(out)
        return False
    return True