from shared_functions import listPromptInquirer, checkBoxPromptInquirer, runCmd, invalidAnswerExit, promptPyInquirer
from argparse import ArgumentParser
import os, sys

choices = ["github", "heroku"]

def main():
    args = takeArgs()
    if not args["to"]:
        args["to"] = listPromptInquirer({
            "name": "deploy_to",
            "question": "where d you want to deploy it?",
            "choices":choices
        })["deploy_to"]
    if not args["path"]:
        # args["path"] = input(f"path of the project folder (current directory: {os.getcwd()}): ")
        args["path"] = promptPyInquirer({
            "type": "input",
            "name": "path",
            "message": f"Path of the project folder: ",
            "default": os.getcwd(),
            "validate": lambda x: "Invalid path" if not os.path.exists(x) else True
        })["path"]
        
    # if not os.path.exists(args["path"]):
    #     print("Invalid path")
    #     sys.exit(5)
    
        
    os.chdir("./") # changing current directory for some reason (idk why)
    print("current directory changed to "+os.getcwd()) #informing user that we've changed directory
    additional_cmd = handleAdditionalCmds(args)
    runCmd(f"py simple_deployer/{args['to']}.py -p {args['path']} {additional_cmd}") # main command

def takeArgs():
    parser = ArgumentParser(prog="github-deployer",
    usage="""""", description="%(prog)s <commands> [options]")
    parser.add_argument("-p", "--path", required=False)
    parser.add_argument("-to", required=False, choices=choices)
    args = parser.parse_args()
    return vars(args)

def handleAdditionalCmds(args):
    additional_cmd = ""
    if args["to"] == "github":
        listAnswers = listPromptInquirer({
                    "name":"command",
                    "question": "Which command you want? (create-update is the default one)",
                    "choices": ["create-update", "update", "delete"]
                })
        additional_cmd += f"{listAnswers['command']} "
        add_addtional_cmds = listPromptInquirer({
            "name":"add_addtional_cmds",
            "question": "Want to add some additional commands?",
            "choices": ["Yes", "No"]
            })["add_addtional_cmds"]
        if(add_addtional_cmds == "Yes"):
                if listAnswers["command"] != "delete":
                    ADD_COLLABORATORS_CHOICE = "Add collaborators"
                    GIT_IGNORE_CHOICE = "Add gitIgnore (ignore files)"
                    VISIBILITY_CHOICE = "Change the visiblity of an existing repository"
                    RESET_TOKEN_CHOICE = "Reset username and token"
                    checkBoxAnswers = checkBoxPromptInquirer({
                        "name": "secondaryOptions",
                        "question": "Add what you want (use space to add stuff and enter to confirm)",
                        "choices": [ADD_COLLABORATORS_CHOICE, GIT_IGNORE_CHOICE, VISIBILITY_CHOICE, RESET_TOKEN_CHOICE]
                    })
                    if(RESET_TOKEN_CHOICE in checkBoxAnswers["secondaryOptions"]):
                        additional_cmd += "-new user token "
                    if(GIT_IGNORE_CHOICE in checkBoxAnswers["secondaryOptions"]):
                        additional_cmd += "-git-ig "
                    if(VISIBILITY_CHOICE in checkBoxAnswers["secondaryOptions"]):
                        additional_cmd += "-visibility "
                    if(ADD_COLLABORATORS_CHOICE in checkBoxAnswers["secondaryOptions"]):
                        additional_cmd += "-ac "
    elif args["to"] == "heroku":
        FRAMEWORK_LANGUAGE_CHOICES = ["nodejs", "flask"]
        listAnswers = listPromptInquirer({
                    "name":"command",
                    "question": "which command you want? (create-update is the default one)",
                    "choices": ["create-update", "update", "delete"],
                }, {
                    "name": "language",
                    "question": "what language/framework are you using?",
                    "choices": FRAMEWORK_LANGUAGE_CHOICES
                })
        additional_cmd += f"{listAnswers['command']} -lang {listAnswers['language']} "
        
        # add_addtional_cmds = listPromptInquirer({
        #     "name":"add_addtional_cmds",
        #     "question": "want to add some additional commands?",
        #     "choices": ["Yes", "No"]
        #     })["add_addtional_cmds"]
        
    return additional_cmd

if __name__ == "__main__":
    main()