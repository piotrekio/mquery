import collections
import dataclasses
import datetime
from decimal import Decimal
from typing import List, Dict

import click


CSV_HEADER_SUFFIX = b"#Data operacji"


@dataclasses.dataclass
class HistoryEntry:
    date: datetime.date
    description: str
    category: str
    amount: Decimal
    currency: str

    @classmethod
    def from_line(cls, line: bytes):
        bits = line.split(b";")
        date = datetime.date(*map(int, bits[0].split(b"-")[:3]))
        description = bits[1].strip(b"\"").strip().decode("windows-1250")
        category = bits[3].strip(b"\"").decode("windows-1250")
        amount = Decimal(bits[4].rsplit(b" ", 1)[0].replace(b",", b".").replace(b" ", b"").decode())
        currency = bits[4].split()[-1].decode("windows-1250")
        return cls(date, description, category, amount, currency)


def read_history(file_name: str) -> List[HistoryEntry]:
    with open(file_name, "rb") as history_file:
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
                history.append(HistoryEntry.from_line(line))

        return history


def group_history_by_date(history: List[HistoryEntry]) -> Dict[datetime.date, List[HistoryEntry]]:
    history_by_date = collections.defaultdict(list)
    for entry in history:
        history_by_date[entry.date].append(entry)
    return history_by_date


def print_history(history: List[HistoryEntry]) -> None:
    history_by_date = group_history_by_date(history)
    for date, entries in history_by_date.items():
        click.secho(str(date), fg="white", bold=True)

        for entry in entries:
            # Amount
            click.secho(
                f"{entry.amount:10} ",
                fg="green" if entry.amount > 0 else "yellow",
                bold=True,
                nl=False,
            )

            # Currency
            click.secho(
                f"{entry.currency} ",
                fg="green" if entry.amount > 0 else "yellow",
                nl=False,
            )

            # Description
            description = entry.description if len(entry.description) < 50 else f"{entry.description[:47]}..."
            click.secho(
                f"{description:50} ",
                fg="cyan",
                nl=False,
            )

            # Category
            click.secho(entry.category, fg="magenta")


@click.command()
@click.argument("file_name", type=click.Path(exists=True))
def main(file_name: str):
    history = read_history(file_name)
    print_history(history)


if __name__ == "__main__":
    main()
