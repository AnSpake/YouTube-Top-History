#!/usr/bin/env python3

import os
import re
import sys
import logging
import argparse
import calendar
import datetime as dt
import pandas
from bs4 import BeautifulSoup


OUTPUT_DIR = "ytb-top-results"
SKIP_WORDS = {
    "en": "Viewed",
    "fr": "Vous avez consulté"
}

MONTHS_FR = {
    'janv': 1, 'janvier': 1,
    'fevr': 2, 'févr': 2, 'fev': 2, 'fév': 2, 'février': 2, 'fevrier': 2,
    'mars': 3,
    'avr': 4, 'avril': 4,
    'mai': 5,
    'juin': 6,
    'juil': 7, 'juillet': 7,
    'aout': 8, 'août': 8,
    'sept': 9, 'septembre': 9,
    'oct': 10, 'octobre': 10,
    'nov': 11, 'novembre': 11,
    'dec': 12, 'déc': 12, 'décembre': 12, 'decembre': 12,
}

MONTHS_EN = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
MONTHS_EN.update({abbr.lower(): i for i, abbr in enumerate(calendar.month_abbr) if abbr})

FR_DATE_RE = re.compile(r'(?P<day>\d{1,2})\s+(?P<month>[A-Za-zéûôàê]+)\.?\s+(?P<year>\d{4}),\s+'
                        r'(?P<hour>\d{1,2}):(?P<minute>\d{2}):(?P<second>\d{2})')
EN_DATE_RE = re.compile(r'(?P<month>[A-Za-z])\s+(?P<day>\d{1,2}),\s+(?P<year>\d{4}),\s+'
                        r'(?P<hour>\d{1,2}):(?P<minute>\d{2}):(?P<second>\d{2})\s*(?P<ampm>AM|PM)?')


def _month_to_int(month_str):
    key = month_str.lower().rstrip('.')
    return MONTHS_EN.get(key) or MONTHS_FR.get(key)


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


def parse_entries(entries, top_amount):
    """
    Reorganize dated entries to sync up with the given time period
    Parse entries from given time period
    Return needed argument to plot figure
    """
    date_groups = time_period.group_entries_per_time(entries)

    for time_period_key in sorted(date_groups.keys()):
        counter = date_groups[time_period_key]
        top_videos = counter.most_common(top_amount)
        data_frame = pandas.DataFrame(top_videos, columns=['Video', 'Plays'])

    return data_frame


def parse_date(text):
    """
    Parse date from Google Takeout FR/EN
    Return a datetime object or None if no match found
    """
    for pattern in (FR_DATE_RE, EN_DATE_RE):
        match = pattern.search(text)
        if not match:
            continue

        month = _month_to_int(match.group('month'))
        if month is None:
            continue

        day = int(match.group('day'))
        year = int(match.group('year'))
        hour = int(match.group('hour'))
        minute = int(match.group('minute'))
        second = int(match.group('second'))

        ampm = match.groupdict().get('ampm')
        if ampm:
            ampm = ampm.upper()
            if ampm == 'PM' and hour != 12:
                hour += 12
            elif ampm == 'AM' and hour == 12:
                hour = 0

        try:
            return dt.datetime(year, month, day, hour, minute, second)
        except ValueError as err:
            logging.error(f"Could not match any date, check the file: {err}")
            continue

    return None


def load_file_html(file_type, file_path):
    """
    Open and read the entries of the given file (HTML)
    """
    entries = []

    if file_type != "html":
        return entries

    # Open the file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_doc = file.read()
    except Exception as err:
        logging.error(f"Could not open the file: {err}")
        return entries

    soup = BeautifulSoup(html_doc, features='html.parser')
    for div in soup.find_all('div', class_='outer-cell mdl-cell mdl-cell--12-col mdl-shadow--2dp'):
        header = div.find('div', class_='header-cell mdl-cell mdl-cell--12-col')

        if not header or not any(ytb_class in header.get_text() for ytb_class in ("YouTube", "YouTube Music")):
            continue

        div_doc = div.find_all('div', class_='content-cell mdl-cell mdl-cell--6-col mdl-typography--body-1')
        if not div_doc:
            continue

        body = div_doc[0]
        text = body.get_text(' ', strip=True)

        # Skip YouTube post watched history (not a video)
        if text.startswith(tuple(SKIP_WORDS.values())):
            continue

        links = body.find_all('a')
        if not links:
            continue

        title = links[0].get_text(strip=True)
        author = links[1].get_text(strip=True).replace(' - Topic', '') if len(links) > 1 else "Unknown Author"
        date = parse_date(text)

        entries.append({'title': f"{title} - {author}", 'date': date})

    return entries


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
    Create output directory
    """
    args = parse_args()

    file_type, file_path = args.file_path
    entries = load_file_html(file_type, file_path)

    # Sanity check on entries
    if not entries:
        logging.error("No entries found in the file. Check if the given file is valid")
        return 1

    entries_date = [e for e in entries if e['date'] is not None]
    if not entries_date:
        logging.error("No dated entries could be found ? Cannot regroup per time period")
        return 1

    logging.info(f"{len(entries)} videos found, {len(entries_date)} with a date")

        time_period = filter_time_period(args)

        try:
            os.makedirs(OUTPUT_DIR)
            parse_entries(entries_date, args.top, time_period)
        except Exception as err:
            logging.error(f"Error while parsing entries: {err}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
