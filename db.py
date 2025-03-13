import sqlite3


def connect_to_db(name: str = "./data/database.db") -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(name)
        return conn
    except sqlite3.Error as e:
        print(e)


def create_db_and_table(name: str = "./data/database.db") -> None:
    try:
        with sqlite3.connect(name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS companies (
                    ric TEXT PRIMARY KEY NOT NULL UNIQUE,
                    company_name TEXT NOT NULL,
                    gics_industry_name TEXT NOT NULL,
                    web_link TEXT,
                    status TEXT DEFAULT 'Not Scraped'
                );      
                """
            )

            conn.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def fill_database(file: str) -> None:
    # Connect to the SQLite database
    conn = connect_to_db()

    # Create a cursor object
    cursor = conn.cursor()

    # Check if the table is empty
    cursor.execute("SELECT COUNT(*) FROM companies")
    count = cursor.fetchone()[0]

    if count == 0:
        print("Filling the database with data from the .xls file...")

        # Read the data from the .xls file
        data = read_data()
