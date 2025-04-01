import argparse

from db import create_db_and_table, fill_database
from scraper import scrape_sites


def app(xls_file: str) -> None:
    # Database part
    create_db_and_table()

    # If database is empty, fill with the data from the .xls file
    fill_database(xls_file)

    # Scraper part
    scrape_sites()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process an xls file.")
    parser.add_argument(
        "--xlsx_file", type=str, help="Path to the xls file", required=True
    )
    args = parser.parse_args()
    app(args.xlsx_file)
