import click

@click.command(
    help="This allows to easily deploy your webapp to heroku!"
)
def main():
    click.echo(click.style("This command no longer works due to the change in the free plan that heroku did!", bg="red"), color=True)
