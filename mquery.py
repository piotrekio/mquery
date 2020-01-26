import collections
import dataclasses
import datetime
from decimal import Decimal
from typing import List, Dict, Union

import click


CSV_HEADER_SUFFIX = b"#Data operacji"
DEFAULT_FILE_ENCODING = "windows-1250"


@dataclasses.dataclass
class HistoryEntry:
    date: datetime.date
    description: str
    category: str
    amount: Decimal
    currency: str

    @classmethod
    def from_line(cls, line: bytes, encoding: str):
        bits = line.split(b";")
        date = datetime.date(*map(int, bits[0].split(b"-")[:3]))
        description = bits[1].strip(b'"').strip().decode(encoding)
        category = bits[3].strip(b'"').decode(encoding)
        amount = Decimal(
            bits[4].rsplit(b" ", 1)[0].replace(b",", b".").replace(b" ", b"").decode()
        )
        currency = bits[4].split()[-1].decode(encoding)
        return cls(date, description, category, amount, currency)


History = List[HistoryEntry]
Filter = Union[str, None]


def read_history(file_path: str, encoding: str) -> History:
    with open(file_path, "rb") as history_file:
        # Skip to CSV data
        for line in history_file:
            if line.startswith(CSV_HEADER_SUFFIX):
                break
        else:
            return []

        # Read CSV data
        history = []
        for line in history_file:
            line = line.strip()
            if line:
                history.append(HistoryEntry.from_line(line, encoding))

        return history


def group_history_by_date(history: History,) -> Dict[datetime.date, History]:
    history_by_date = collections.defaultdict(list)
    for entry in history:
        history_by_date[entry.date].append(entry)
    return history_by_date


def print_entry(entry: HistoryEntry) -> None:
    if entry.amount > 0:
        click.secho(f"{entry.amount:10} ", fg="green", bold=True, nl=False)
        click.secho(f"{entry.currency} ", fg="green", nl=False)
    else:
        click.secho(f"{entry.amount:10} ", fg="yellow", bold=True, nl=False)
        click.secho(f"{entry.currency} ", fg="yellow", nl=False)
    click.secho(
        f"{entry.description:50} "
        if len(entry.description) <= 50
        else f"{entry.description[:47]}... ",
        fg="cyan",
        nl=False,
    )
    click.secho(entry.category, fg="magenta")


def print_history(history: History) -> None:
    history_by_date = group_history_by_date(history)
    for date, entries in history_by_date.items():
        click.secho(str(date), fg="white", bold=True)
        for entry in entries:
            print_entry(entry)


def filter_history(
    history: History, filter_description: Filter, filter_category: Filter
):
    new_history: History = []
    filter_description: Filter = filter_description and filter_description.lower()
    filter_category: Filter = filter_category and filter_category.lower()
    for entry in history:
        if filter_description and filter_description not in entry.description.lower():
            continue
        if filter_category and filter_category not in entry.category.lower():
            continue
        new_history.append(entry)
    return new_history


@click.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("-e", "--encoding", default=DEFAULT_FILE_ENCODING)
@click.option("-d", "--filter-description", default=None)
@click.option("-c", "--filter-category", default=None)
def main(
    file_path: str, encoding: str, filter_description: Filter, filter_category: Filter
):
    history = read_history(file_path, encoding)
    history = filter_history(history, filter_description, filter_category)
    print_history(history)


if __name__ == "__main__":
    main()
