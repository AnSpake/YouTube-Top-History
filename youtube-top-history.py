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
