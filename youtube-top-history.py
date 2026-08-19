#!/usr/bin/env python3

import os
import re
import sys
import logging
import argparse
import calendar
import datetime as dt
from typing import Optional
from collections import defaultdict, Counter
from dataclasses import dataclass
import xml.etree.ElementTree as ET
import pandas
import seaborn
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from tqdm import tqdm

# FIXME: Uncomment/modify as needed
# logging.basicConfig(level=logging.INFO)

FONT_COMPATIBLE = [
    "Noto Sans",
    "Droid Sans Fallback",
    "Noto Sans Math",
    "IPAexGothic", "IPAGothic",
    "Yu Gothic", "MS Gothic",
    "Hiragino Sans", "Hiragino Kaku Gothic Pro",
    "WenQuanYi Zen Hei", "Microsoft YaHei"
]

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


def _find_extra_font(font_available):
    for font in FONT_COMPATIBLE:
        if font in font_available:
            return font
    return None


def setup_compatible_font():
    """
    Search for available font on the system and if there is any compatible to
    handle missing glyph.
    Depends on the fonts installed on your system.
    """
    plt.rcParams['svg.fonttype'] = 'none'
    font_available = {f.name for f in fm.fontManager.ttflist}

    EXTRA_FONT = find_extra_font(font_available)

    if EXTRA_FONT:
        current_font = plt.rcParams['font.family']

        # Configuration per system allow more flexibility in handling specific cases
        match sys.platform:
            case "linux":
                fonts = [
                    font for font in (
                        EXTRA_FONT,
                        FONT_COMPATIBLE[1],
                        FONT_COMPATIBLE[2],
                        *current_font)
                    if font in font_available
                        ]
            # case "darwin": FIXME
            # case for windows FIXME
            case _:
                fonts = [
                    font for font in (
                        EXTRA_FONT,
                        FONT_COMPATIBLE[1],
                        *current_font)
                    if font in font_available
                        ]

        plt.rcParams['font.family'] = fonts

    else:
        logging.warning(
            "Warning: no CJK font found on this system so titles with foreign letters will show as missing glyps -> □."
            "After installing the missing font, refresh your system's font cache AND matplotlib cache.")


@dataclass
class TimePeriod:
    """
    Given the mess that are the available argument combinaisons,
    using a class to help reformat the wanted time period to extract data from.

    group_by: 'none' | 'month' | 'year'
    """
    month: Optional[int] = None
    year: Optional[int] = None
    group_by: str = None

    def filter_entries_per_time(self, entries):
        res = entries
        if self.year is not None:
            res = [entry for entry in res if entry['date'].year == self.year]
        if self.month is not None:
            res = [entry for entry in res if entry['date'].month == self.month]
        return res

    def group_entries_per_time(self, entries):
        key = ""
        groups = defaultdict(Counter)
        for entry in self.filter_entries_per_time(entries):
            match self.group_by:
                case 'month':
                    key = entry['date'].strftime('%Y-%m')
                case 'year':
                    key = entry['date'].strftime('%Y')
                case _:
                    key = 'all'
            groups[key][(entry['title'], entry['author'], entry['url'])] += 1

        return groups


def underline_title_link_svg(output_path):
    """
    Overkill function to underline the click-able title video
    by editing the svg file
    Pros: don't depend on matplot if they change the output of the svg file
    """
    ET.register_namespace('', "http://www.w3.org/2000/svg")
    ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")

    xml_tree = ET.parse(output_path)
    xml_root = xml_tree.getroot()

    namespace = "{http://www.w3.org/2000/svg}"

    for link in xml_root.iter(namespace + 'a'):
        for text in link.iter(namespace + 'text'):
            style = text.get('style', "")
            text.set('style', style + ";text-decoration:underline")

    xml_tree.write(output_path, encoding="utf-8", xml_declaration=True)


def add_authors(ax, authors):
    """
    Another overkill function to add the author in the second row while
    not make it have the same text properties as the title (url click-able and
    blue color)
    Also make the y label print on the top of the "list"
    """
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    labels = ax.get_yticklabels()

    for label, author in zip(ax.get_yticklabels(), authors):
        x, y = label.get_position()

        ax.annotate(author, xy=(x, y), xytext=(-1, 0),
                    textcoords='offset fontsize',
                    ha='right', va='top',
                    fontsize=label.get_fontsize())

    # Add "video title" y label above the items
    first_label = labels[0]
    flabel_fontsize = first_label.get_fontsize()
    bbox = first_label.get_window_extent(renderer=renderer)

    x_fig, y_fig = fig.transFigure.inverted().transform((bbox.x1 - flabel_fontsize, bbox.y1 + flabel_fontsize * 2))
    fig.text(x_fig, y_fig, "video title",
             ha='right', va='bottom',
             fontsize=flabel_fontsize)


def figure_top_videos(data_frame, top_amount, time_period_key):
    """
    Draw scoreboard of top videos
    """
    df_top_amount = data_frame.head(top_amount)
    colors = seaborn.color_palette('magma', len(df_top_amount))

    row_height = 0.5
    min_height = 4
    fig_height = max(min_height,  row_height * len(df_top_amount))
    fig_width = 10

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)

    df_top_amount.plot(kind='barh', x='Video', y='Plays', legend=False, color=colors, ax=ax)

    for i, v in enumerate(df_top_amount['Plays']):
        plt.text(v, i, str(v))

    ax.set_title(f"Top {top_amount} - {time_period_key}")
    ax.set_xlabel("nbr of play")
    ax.set_ylabel("")

    ax.invert_yaxis()

    add_authors(ax, df_top_amount['Author'])
    bars = ax.patches

    for video, url, b in zip(ax.get_yticklabels(), df_top_amount['Url'], bars):
        x = video.get_position()[0]
        y = b.get_y() + b.get_height()

        video.set_position((x, y))
        video.set_va('bottom')

        if url:
            video.set_url(url)
            video.set_color("#0645AD")
            video.set_fontweight('normal')

    output_path = os.path.join(OUTPUT_DIR, f"top_{top_amount}_{time_period_key}.svg")
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)

    underline_title_link_svg(output_path)

    logging.info(f"Figure generated for {time_period_key} -> {output_path}")


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


def parse_entries(entries, top_amount, time_period, pbar):
    """
    Reorganize dated entries to sync up with the given time period
    Parse entries from given time period
    Return needed argument to plot figure
    """
    date_groups = time_period.group_entries_per_time(entries)

    for time_period_key in sorted(date_groups.keys()):
        counter = date_groups[time_period_key]
        top_videos = counter.most_common(top_amount)

        data_frame = pandas.DataFrame([
                {
                    'Video': title,
                    'Author': author,
                    'Url': url,
                    'Plays': plays
                }
                for (title, author, url), plays in top_videos])

        figure_top_videos(data_frame, top_amount, time_period_key)
        pbar.update(1)
        pbar.refresh()

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


def load_file_html(file_type, file_path, pbar):
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
    pbar.update(20)
    pbar.refresh()

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
        url = links[0].get('href')

        entries.append({'title': title, 'author': author, 'date': date, 'url': url})
        pbar.update(1)
        pbar.refresh()

    return entries


def filter_time_period(args):
    """
    Given the numerous type of arguments
    Unify it to a workable variable
    We can regroup all the different cases with 2 groups
        - Figure per month
        - Figure per year
    """
    today = dt.date.today()

    TIME_TABLE = [
        (lambda a: a.today,             lambda a: TimePeriod(month=today.month, year=today.year, group_by='month')),
        (lambda a: a.month is not None, lambda a: TimePeriod(month=a.month, year=args.year or today.year, group_by='month')),
        (lambda a: a.year is not None,  lambda a: TimePeriod(year=args.year, group_by='year')),
        (lambda a: a.all_month,         lambda a: TimePeriod(year=args.year or today.year, group_by='month')),
        (lambda a: a.all_year,          lambda a: TimePeriod(group_by='year')),
        (lambda a: a.all,               lambda a: TimePeriod(group_by='month')),
    ]

    for args_exist, filter_time in TIME_TABLE:
        if args_exist(args):
            return filter_time(args)
    return TimePeriod()


def parse_args():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-path', required=True, type=parse_file,
                        help="Path to your watch_history file")
    parser.add_argument('--top', required=False, type=int, default=10,
                        help="Number of top videos for the scoreboard")
    parser.add_argument('--today', required=False, action='store_true', default=False,
                        help="Get the scoreboard of the current month")

    parser.add_argument('--month', required=False, type=parse_month,
                        help="Get the scoreboard of the given month of current/given year")
    parser.add_argument('--year', required=False, type=parse_year,
                        help="Get the scoreboard of the given year")

    parser.add_argument('--all-month', required=False, action='store_true', default=False,
                        help="Get the scoreboard for each month of current/given year")
    parser.add_argument('--all-year', required=False, action="store_true", default=False,
                        help="Get the scoreboard for each years")
    parser.add_argument('--all', required=False, action='store_true', default=False,
                        help="Get the scoreboard for each years + each months of every years")

    args = parser.parse_args()
    return args


def main():
    """
    Main function
    Create output directory
    """
    args = parse_args()

    # Preference for manual deletion/overwrite
    if os.path.exists(OUTPUT_DIR):
        logging.error(f"Result folder {OUTPUT_DIR} -> Delete it to proceed.")
        return 1

    file_type, file_path = args.file_path

    pbar = tqdm(range(50000))

    # Handle special characters
    setup_compatible_font()
    pbar.update(5)
    pbar.refresh()

    entries = load_file_html(file_type, file_path, pbar)

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
    pbar.update(5)
    pbar.refresh()

    try:
        os.makedirs(OUTPUT_DIR)
        parse_entries(entries_date, args.top, time_period, pbar)
    except Exception as err:
        logging.exception(f"Error while parsing entries: {err}")

    pbar.n = pbar.total
    pbar.refresh()
    return 0


if __name__ == "__main__":
    sys.exit(main())
