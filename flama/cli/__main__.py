import click
import typing
import subprocess
import shlex


def uvicorn(*args) -> typing.List[str]:
    return shlex.split("uvicorn") + list(args)


@click.group()
def cli():
    """
    Flama 🔥.
    """
    ...


@click.command()
@click.argument("flama-app", envvar="FLAMA_APP")
def run(app_path: str):
    """
    Run an API.

    FLAMA_APP is the path to the Flama object to be served, e.g. examples.hello_flama:app
    """
    subprocess.run(uvicorn(app_path))


cli.add_command(run)


@click.command()
def dev():
    """
    Run an API in development mode.
    """
    ...


cli.add_command(dev)


@click.command()
def serve():
    """
    Run an API for a ML Model.
    """
    ...


cli.add_command(serve)


if __name__ == "__main__":
    cli()
