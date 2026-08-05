#!/usr/bin/env python3

import sys
import argparse
import calendar
import datetime as dt


def parse_file(file_path):
    if file_path.endswith('json'):
        return 'json', file_path

    if file_path.endswith('html'):
        return 'html', file_path

    raise argparse.ArgumentTypeError(f"Invalid file: {file_path} is not a valid file (can't guess file type)")


def parse_month(month_raw):
    """
    Argparse helper
    Accept month argument in either string or integer
    """
    month_raw = month_raw.strip()

    if month_raw.isdigit():
        month = int(month_raw)
        if 1 <= month <= 12:
            return month
        raise argparse.ArgumentTypeError(f"Invalid month: {month_raw} is not a valid month number")

    MONTHS = {month_str.lower(): i for i, month_str in enumerate(calendar.month_name) if month_str}
    MONTHS.update({abbr.lower(): i for i, abbr in enumerate(calendar.month_abbr) if abbr})
    month = MONTHS.get(month_raw)
    if month is not None:
        return month
    raise argparse.ArgumentTypeError(f"Invalid month: {month_raw} is not a valid month name")


def parse_year(year_raw):
    """
    Argparse helper
    Accept valid years -> 2005 to today
    """
    year_raw = year_raw.strip()

    if year_raw.isdigit():
        year = int(year_raw)
        if 2005 <= year <= dt.date.today().year:
            return year
        raise argparse.ArgumentTypeError(f"Invalid year: {year_raw} (No YouTube data for that year)")

    raise argparse.ArgumentTypeError(f"Invalid year: {year_raw} is not a valid year number")


def parse_args():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-path', required=True, type=parse_file,
                        help="Path to your watch_history file")
    parser.add_argument('--top', required=False, type=int, default=10,
                        help="Number of top videos for the scoreboard")
    parser.add_argument('--today', required=False, action="store_true", default=False,
                        help="Get the scoreboard of the current month")

    parser.add_argument('--month', required=False, type=parse_month,
                        help="Get the scoreboard of the given month of current/given year")
    parser.add_argument('--year', required=False, type=parse_year,
                        help="Get the scoreboard of the given year")

    parser.add_argument('--all-month', required=False, action="store_true", default=False,
                        help="Get the scoreboard for each month of current/given year")
    parser.add_argument('--all-year', required=False, action="store_true", default=False,
                        help="Get the scoreboard for each years")
    parser.add_argument('--all', required=False, action="store_true", default=False,
                        help="Get the scoreboard for each years + each months of every years")

    args = parser.parse_args()
    return args


def main():
    """
    Main function
    """
    args = parse_args()

    return 0


if __name__ == "__main__":
    sys.exit(main())
