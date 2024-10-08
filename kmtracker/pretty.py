from rich.console import Console
from rich.table import Table


console = Console()


def print_rows(rows: list):
    table = Table()
    for col in rows[0].keys():
        table.add_column(col)
    for row in rows:
        table.add_row(*list(map(str, row)))
    console.print(table)
