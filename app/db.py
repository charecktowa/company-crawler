import sqlite3

from utils import read_xlsx

DATABASE_PATH = "./data/database.db"


def connect_to_db(name: str = DATABASE_PATH) -> sqlite3.Connection:
    try:
        conn = sqlite3.connect(name)
        return conn
    except sqlite3.Error as e:
        print(e)


def create_db_and_table(name: str = DATABASE_PATH) -> None:
    try:
        with sqlite3.connect(name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS companies(
                    ric TEXT PRIMARY KEY NOT NULL UNIQUE,
                    company_name TEXT NOT NULL,
                    industry_type TEXT NOT NULL,
                    web_link TEXT,
                    status TEXT DEFAULT "Not Scraped"
                );
                """
            )

            conn.commit()
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def get_data_from_db(name: str = DATABASE_PATH) -> list:
    try:
        conn = connect_to_db(name)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies")
        data = cursor.fetchall()
        return data
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def get_link_from_db(name: str = DATABASE_PATH) -> list:
    try:
        conn = connect_to_db(name)
        cursor = conn.cursor()
        cursor.execute("SELECT web_link FROM companies")
        data = cursor.fetchall()
        return data
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def count_data_from_db(name: str = DATABASE_PATH) -> int:
    try:
        conn = connect_to_db(name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM companies")
        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def get_data_limit_offset(limit: int, offset: int, name: str = DATABASE_PATH) -> list:
    try:
        conn = connect_to_db(name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM companies LIMIT {limit} OFFSET {offset}")
        data = cursor.fetchall()
        return data
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def insert_data(data: list, conn: sqlite3.Connection) -> None:
    # Extract all elements from data to later be saved into the database
    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO companies(ric, company_name, industry_type, web_link) VALUES (?, ?, ?, ?)",
            data,
        )
        conn.commit()
    except sqlite3.Error as e:
        print(e)


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

        data = read_xlsx(file)

        insert_data(data, conn)

    # Close the connection
    if conn:
        conn.close()
