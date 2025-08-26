import typer
from rich.console import Console
from rich.table import Table

import easydiffraction as ed

console = Console()
app = typer.Typer()


@app.command('list-tutorials')
def list_tutorials():
    """List available tutorial notebooks."""
    table = Table('No.', 'Notebook')
    for idx, tutorial in enumerate(ed.list_tutorials()):
        table.add_row(str(idx + 1), tutorial)
    console.print(table)


@app.command('fetch-tutorials')
def fetch_tutorials():
    """Download and extract tutorial notebooks."""
    ed.fetch_tutorials()


if __name__ == '__main__':
    app()
