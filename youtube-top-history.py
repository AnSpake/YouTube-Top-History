#!/usr/bin/env python3

import sys
import argparse


def parse_args():
    """
    Parse CLI arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--file-path', required=True,
                        help="Path to your watch_history file")
    parser.add_argument('--top', required=False, type=int, default=10,
                        help="Number of top videos for the scoreboard")
    parser.add_argument('--today', required=False,
                        help="Get the scoreboard of the current month")

    # FIXME: default = current month, current year
    parser.add_argument('--month', required=False,
                        help="Get the scoreboard of the given month")
    parser.add_argument('--year', required=False,
                        help="Get the scoreboard of the given year")

    parser.add_argument('--all-month', required=False,
                        help="Get the scoreboard for each month of current/given year")
    parser.add_argument('--all-year', required=False,
                        help="Get the scoreboard for each years")
    parser.add_argument('--all', required=False,
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
