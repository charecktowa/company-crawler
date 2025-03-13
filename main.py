from db import create_db_and_table, fill_database


def main(xls_fil: str) -> None:
    # Connect to database
    create_db_and_table()

    # If database is empty, fill with the data from the CSV file
    fill_database()


if __name__ == "__main__":
    main()
