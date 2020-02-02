import collections
import dataclasses
import datetime
from decimal import Decimal
from typing import List, Dict, Union

import click


__version__ = "0.1.0"

DEFAULT_CSV_HEADER_SUFFIX = "#Data operacji"
DEFAULT_CURRENCY = "PLN"
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


FilterDate = Union[datetime.date, None]
FilterDecimal = Union[Decimal, None]
FilterString = Union[str, None]
History = List[HistoryEntry]


class DateParamType(click.ParamType):
    name = "date"

    def convert(
        self, value: str, param: click.core.Option, ctx: click.core.Context
    ) -> FilterDate:
        if not value:
            return None
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            self.fail(f"{value!r} is not a valid date", param, ctx)


class DecimalParamType(click.ParamType):
    name = "decimal"

    def convert(
        self, value: str, param: click.core.Option, ctx: click.core.Context
    ) -> FilterDecimal:
        if not value:
            return None
        try:
            return Decimal(value)
        except TypeError:
            self.fail(f"{value!r} is not a valid decimal number", param, ctx)


DATE = DateParamType()
DECIMAL = DecimalParamType()


def read_history(file_path: str, encoding: str, csv_header_suffix: str) -> History:
    with open(file_path, "rb") as history_file:
        # Skip to CSV data
        for line in history_file:
            if line.startswith(csv_header_suffix.encode()):
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


def filter_history(
    history: History,
    amount_from: FilterDecimal,
    amount_to: FilterDecimal,
    category: FilterString,
    currency: FilterString,
    date_from: FilterDate,
    date_to: FilterDate,
    description: FilterString,
):
    new_history: History = []
    category: FilterString = category and category.lower()
    description: FilterString = description and description.lower()
    for entry in history:
        if amount_from and abs(entry.amount) < amount_from:
            continue
        if amount_to and abs(entry.amount) > amount_to:
            continue
        if category and category not in entry.category.lower():
            continue
        if currency and entry.currency != currency:
            continue
        if date_from and entry.date < date_from:
            continue
        if date_to and entry.date > date_to:
            continue
        if description and description not in entry.description.lower():
            continue
        new_history.append(entry)
    return new_history


def print_entry(entry: HistoryEntry) -> None:
    if entry.amount > 0:
        click.secho(f"{entry.amount:+10} ", fg="green", bold=True, nl=False)
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


def print_history(history: History, reverse_order: bool) -> None:
    history_by_date = group_history_by_date(history)
    dates = history_by_date.keys()
    if reverse_order:
        dates = reversed(dates)
    for date in dates:
        entries = history_by_date[date]
        click.secho(str(date), fg="white", bold=True)
        for entry in entries:
            print_entry(entry)


def print_summary(history: History, currency: str) -> None:
    income = expenses = 0
    for entry in history:
        if entry.currency == currency:
            if entry.amount > 0:
                income += entry.amount
            else:
                expenses += entry.amount
    balance = income + expenses
    if balance > 0:
        balance_color = "green"
    elif balance < 0:
        balance_color = "yellow"
    else:
        balance_color = "white"
    print()
    click.echo("Income:    ", nl=False)
    click.secho(click.style(f"{income:+12}", fg="green"))
    click.echo("Expenses:  ", nl=False)
    click.secho(f"{expenses:+12}", fg="yellow")
    click.secho("Balance:   ", bold=True, nl=False)
    click.secho(f"{balance:+12}", fg=balance_color, bold=True)


@click.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("-af", "--amount-from", type=DECIMAL, default=None)
@click.option("-at", "--amount-to", type=DECIMAL, default=None)
@click.option("-c", "--category", default=None)
@click.option("-df", "--date-from", type=DATE, default=None)
@click.option("-dt", "--date-to", type=DATE, default=None)
@click.option("-d", "--description", default=None)
@click.option("-e", "--encoding", default=DEFAULT_FILE_ENCODING)
@click.option("-h", "--csv-header-suffix", default=DEFAULT_CSV_HEADER_SUFFIX)
@click.option("-r", "--reverse-order", is_flag=True)
@click.option("-s", "--summary", is_flag=True)
@click.option("-u", "--currency", default=DEFAULT_CURRENCY)
@click.version_option(__version__)
def main(
    file_path: str,
    encoding: str,
    amount_from: FilterDecimal,
    amount_to: FilterDecimal,
    category: FilterString,
    date_from: FilterDate,
    date_to: FilterDate,
    description: FilterString,
    reverse_order: bool,
    summary: bool,
    csv_header_suffix: str,
    currency: FilterString,
):
    history = read_history(file_path, encoding, csv_header_suffix)
    history = filter_history(
        history,
        amount_from,
        amount_to,
        category,
        currency,
        date_from,
        date_to,
        description,
    )
    print_history(history, reverse_order)
    if summary:
        print_summary(history, currency)


if __name__ == "__main__":
    main()
