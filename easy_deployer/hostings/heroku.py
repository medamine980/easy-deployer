import click

from easy_deployer.utilities.interface import print_color

@click.command(
    help="This allows to easily deploy your webapp to heroku!"
)
def main():
    print_color("This command no longer works due to the change in the free plan that heroku did!", bg="red")