from typing import Callable

from InquirerPy import inquirer


def text_input(
        message: str, 
        default: str="", 
        invalid_message: str = None,
        validate: Callable[[str], None] = None
        ):
    return inquirer.text(
        message=message,
        default=default,
        validate=validate,
        invalid_message=invalid_message,
    ).execute()





def path_input(
        message: str, 
        default: str="", 
        invalid_message: str = None,
        only_files: bool = False,
        only_directories: bool = False,
        validate: Callable[[str], None] = None
        ):
    return inquirer.filepath(
        message=message,
        default=default,
        validate=validate,
        invalid_message=invalid_message,
        only_files=only_files,
        only_directories=only_directories
    ).execute()

def confirm_input(
        message: str, 
        default: str="", 
        invalid_message: str = None,
        validate: Callable[[str], None] = None
        ):
    return inquirer.confirm(
        message=message,
        default=default,
        validate=validate,
        invalid_message=invalid_message,
    ).execute()

def select_input(
        message: str,
        default: str="",
        choices: list=[]
):
    return inquirer.select(
        message=message,
        default=default,
        choices=choices
    ).execute()

def print_warning(*text,**keywords):
    print("""
    ******************************************
                  _   __               __    
        \  /\  / /_\ |__| |\ | | |\ | |  __
         \/  \/ /   \|  \ | \| | | \| |__|  """)
    print("\t",*text, **keywords)
    print("""
    *******************************************""")