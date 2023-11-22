import click

from typing import Callable

from InquirerPy import inquirer


def text_input(
        message: str, 
        instruction: str="",
        default: str="", 
        multiline: bool = False,
        invalid_message: str = None,
        validate: Callable[[str], None] = None
        ) -> str:
    return inquirer.text(
        message=message,
        instruction=instruction,
        default=default,
        multiline=multiline,
        validate=validate,
        invalid_message=invalid_message,
        multicolumn_complete=False
    ).execute()





def path_input(
        message: str, 
        instruction: str = "",
        default: str="", 
        invalid_message: str = None,
        only_files: bool = False,
        only_directories: bool = False,
        validate: Callable[[str], None] = None
        ) -> str:
    return inquirer.filepath(
        message=message,
        instruction=instruction,
        default=default,
        validate=validate,
        invalid_message=invalid_message,
        only_files=only_files,
        only_directories=only_directories,
    ).execute()

def confirm_input(
        message: str, 
        default: str=False
        ):
    return inquirer.confirm(
        message=message,
        default=default
    ).execute()

def select_input(
        message: str,
        default: str="",
        choices: list=[]
) -> str:
    return inquirer.select(
        message=message,
        default=default,
        choices=choices
    ).execute()

def print_color(text, fg="white", bg:str or tuple = None, bold: bool = None, underline: bool = None,
                overline: bool = None, blink: bool = None, italic: bool = None, dim: bool = None,
                reverse: bool = None, strikethrough: bool = None, reset: bool = True) -> None:
    click.secho(text, color=True, fg=fg, bg=bg, bold=bold, underline=underline, overline=overline,
                blink=blink, italic=italic, dim=dim, reverse=reverse, strikethrough=strikethrough, reset=reset)

def print_warning(*text,**keywords):
    print("""
    ******************************************
                  _   __               __    
        \  /\  / /_\ |__| |\ | | |\ | |  __
         \/  \/ /   \|  \ | \| | | \| |__|  """)
    print("\t",*text, **keywords)
    print("""
    *******************************************""")