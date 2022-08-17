import psycopg
import typer
import uvicorn
from typer import Exit, Option, Typer

from . import config, db

app = Typer()


@app.command()
def migrate(up: bool = Option(True, "--up/--down")):
    """Apply or reverse the schema migrations."""
    operation = db.migrations.create_schema if up else db.migrations.delete_schema
    settings = config.load_settings()

    with db.create_connection(settings) as conn:
        try:
            operation(conn)
        except (psycopg.errors.DuplicateObject, psycopg.errors.DuplicateTable):
            typer.echo("Migrations already applied", err=True)
            raise Exit(code=1)
        else:
            typer.echo("Migrations applied successfully")


@app.command()
def run(host: str = "127.0.0.1", reload: bool = Option(False, "--reload/--no-reload")):
    """Start the raffle API server on the given interface."""
    uvicorn.run("raffle.api:app", host=host, reload=reload)


if __name__ == "__main__":
    app()
