from .version_control import github_main
from .hostings import heroku_main

__version__: str = "0.1.13"

def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    print(f'Version {__version__}')
    ctx.exit()