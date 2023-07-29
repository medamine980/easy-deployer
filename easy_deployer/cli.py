import click
from easy_deployer import github_main, heroku_main, print_version
from easy_deployer.utilities.interface import select_input


@click.group(invoke_without_command=True)
@click.option("-v", "--version", is_flag=True, callback=print_version, 
              expose_value=False, is_eager=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        deploy_to = select_input("Select where you want to deploy to", choices=["github"])
        if deploy_to == "github":
            github_main()
    # ctx.invoke(github_main, path="4")

cli.add_command(github_main, "github")
cli.add_command(heroku_main, "heroku")

# if __name__ == "__main__":
#     cli.add_command(github_main, "github")
#     cli.add_command(heroku_main, "heroku")
#     cli()