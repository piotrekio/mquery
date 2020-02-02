import datetime
from decimal import Decimal

import factory
import pytest

from mquery import HistoryEntry, filter_history, group_history_by_date, read_history


class HistoryEntryFactory(factory.Factory):
    class Meta:
        model = HistoryEntry

    date = factory.Faker("past_date", start_date="-7d")
    description = factory.Faker("sentence", nb_words=8)
    category = factory.Faker("sentence", nb_words=3)
    amount = factory.Faker(
        "pydecimal", left_digits=3, right_digits=2, positive=False, max_value=-1
    )
    currency = "PLN"


def test_read_history(tmpdir):
    test_data = b"""
# First line of the header
#
# Last line of the header
2015-10-15;LOREM;;;-1234,50 PLN
2019-04-30;"LOREM IPSUM DOLOR SIT AMET";;FOO;-0,12 PLN
2020-12-03;;;"FOO BAR";6543,21 PLN

"""
    expected_history = [
        HistoryEntry(
            datetime.date(2015, 10, 15), "LOREM", "", Decimal("-1234.50"), "PLN"
        ),
        HistoryEntry(
            datetime.date(2019, 4, 30),
            "LOREM IPSUM DOLOR SIT AMET",
            "FOO",
            Decimal("-0.12"),
            "PLN",
        ),
        HistoryEntry(
            datetime.date(2020, 12, 3), "", "FOO BAR", Decimal("6543.21"), "PLN"
        ),
    ]
    test_data_path = tmpdir.join("test_data.csv")
    with open(test_data_path, "wb") as test_data_file:
        test_data_file.write(test_data)
    history = read_history(test_data_path, "utf-8", "# Last line")
    assert history == expected_history


def test_group_history_by_date_returns_entries_grouped_by_date():
    history = HistoryEntryFactory.create_batch(10)
    grouped = group_history_by_date(history)
    for date, entries in grouped.items():
        for entry in entries:
            assert entry.date == date


def test_group_history_by_date_returns_all_entries():
    history = HistoryEntryFactory.create_batch(10)
    grouped = group_history_by_date(history)
    assert len(history) == sum([len(entries) for entries in grouped.values()])


TEST_HISTORY = [
    HistoryEntry(  # 0
        date=datetime.date(2020, 1, 10),
        amount=Decimal("150.0"),
        currency="PLN",
        category="foo",
        description="lorem ipsum",
    ),
    HistoryEntry(  # 1
        date=datetime.date(2020, 1, 9),
        amount=Decimal("-100.0"),
        currency="PLN",
        category="foo",
        description="dolor ipsum",
    ),
    HistoryEntry(  # 2
        date=datetime.date(2020, 1, 9),
        amount=Decimal("-40.0"),
        currency="PLN",
        category="foo",
        description="dolor sit amet",
    ),
    HistoryEntry(  # 3
        date=datetime.date(2020, 1, 8),
        amount=Decimal("-150.0"),
        currency="PLN",
        category="bar",
        description="lorem ipsum",
    ),
    HistoryEntry(  # 4
        date=datetime.date(2020, 1, 8),
        amount=Decimal("-90.0"),
        currency="EUR",
        category="foo",
        description="lorem ipsum",
    ),
    HistoryEntry(  # 5
        date=datetime.date(2020, 1, 7),
        amount=Decimal("-90.0"),
        currency="PLN",
        category="bar",
        description="dolor sit amet",
    ),
]


@pytest.mark.parametrize(
    "history, filters, expected_history",
    [
        (
            TEST_HISTORY,
            {"amount_from": 100},
            [TEST_HISTORY[0], TEST_HISTORY[1], TEST_HISTORY[3]],
        ),
        (
            TEST_HISTORY,
            {"amount_to": 95},
            [TEST_HISTORY[2], TEST_HISTORY[4], TEST_HISTORY[5]],
        ),
        (
            TEST_HISTORY,
            {"amount_from": 80, "amount_to": 95},
            [TEST_HISTORY[4], TEST_HISTORY[5]],
        ),
        (TEST_HISTORY, {"category": "ar"}, [TEST_HISTORY[3], TEST_HISTORY[5]],),
        (TEST_HISTORY, {"currency": "EUR"}, [TEST_HISTORY[4]],),
        (
            TEST_HISTORY,
            {"description": "ipsum"},
            [TEST_HISTORY[0], TEST_HISTORY[1], TEST_HISTORY[3], TEST_HISTORY[4]],
        ),
        (
            TEST_HISTORY,
            {"date_from": datetime.date(2020, 1, 9)},
            [TEST_HISTORY[0], TEST_HISTORY[1], TEST_HISTORY[2]],
        ),
        (
            TEST_HISTORY,
            {"date_to": datetime.date(2020, 1, 8)},
            [TEST_HISTORY[3], TEST_HISTORY[4], TEST_HISTORY[5]],
        ),
        (
            TEST_HISTORY,
            {
                "date_from": datetime.date(2020, 1, 8),
                "date_to": datetime.date(2020, 1, 9),
            },
            [TEST_HISTORY[1], TEST_HISTORY[2], TEST_HISTORY[3], TEST_HISTORY[4]],
        ),
    ],
)
def test_filter_history_returns_history_without_not_matching_entries(
    history, filters, expected_history
):
    filtered_history = filter_history(history, **filters)
    assert filtered_history == expected_history
