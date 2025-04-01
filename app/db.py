import sqlite3
from urllib.parse import urlparse

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

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scraped_data(
                    ric TEXT PRIMARY KEY NOT NULL UNIQUE,
                    web_link TEXT,
                    status TEXT DEFAULT "Not Scraped",
                    scraped_purpose TEXT,
                    generated_purpose TEXT,
                    --- This is new---
                    paragraph TEXT,
                    confidence INTEGER,
                    overview TEXT,
                    focus TEXT,
                    inference TEXT,
                    --- End of new ---

                    FOREIGN KEY (ric) REFERENCES companies(ric),
                    FOREIGN KEY (web_link) REFERENCES companies(web_link),
                    FOREIGN KEY (status) REFERENCES companies(status)
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


def get_data_status(url: str, name: str = DATABASE_PATH) -> str | None:
    """
    Return the status string if the company is found, or None if not found.
    """
    try:
        conn = connect_to_db(name)
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM companies WHERE web_link = ?", (url,))
        row = cursor.fetchone()
        if row is None:
            return None
        return row[0]
    except sqlite3.Error as e:
        print(e)
        return None
    finally:
        if conn:
            conn.close()


def get_data_from_db_by_status(status: str, name: str = DATABASE_PATH) -> list:
    try:
        conn = connect_to_db(name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM companies WHERE status = '{status}'")
        data = cursor.fetchall()
        return data
    except sqlite3.Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def get_data_from_db_by_link(link: str, name: str = DATABASE_PATH) -> list:
    try:
        conn = connect_to_db(name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM companies WHERE web_link = '{link}'")
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


def update_purpose(
    url: str,
    purpose: str,
    paragraph: str,
    confidence: int,
    overview: str,
    focus: str,
    inference: str,
) -> None:
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE scraped_data
            SET scraped_purpose = ?,
                paragraph = ?,
                confidence = ?,
                overview = ?,
                focus = ?,
                inference = ?
            WHERE ric = (
                SELECT ric FROM companies WHERE web_link = ?
            )
            """,
            (purpose, paragraph, confidence, overview, focus, inference, url),
        )

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in update_purpose: {e}")
    finally:
        if conn:
            conn.close()


def save_to_db(url: str, about_url: str, status: str = "SCRAPED") -> None:
    """
    Update the 'companies' table for the given 'url' to set its status,
    then upsert a row in 'scraped_data' with the discovered about_url and the same status.
    """
    conn = None
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        # 1. Find the company's RIC by matching its web_link to url
        cursor.execute("SELECT ric FROM companies WHERE web_link = ?", (url,))
        row = cursor.fetchone()

        if not row:
            print(f"No matching row found in 'companies' for the given URL: {url}")
            return

        ric = row[0]  # The RIC from the companies table

        # 2. Update companies table to set its status
        cursor.execute("UPDATE companies SET status = ? WHERE ric = ?", (status, ric))

        # 3. Upsert (INSERT or IGNORE + UPDATE) in 'scraped_data' for the same RIC
        #    We'll first INSERT IGNORE in case there's no row for this RIC,
        #    then UPDATE to make sure web_link and status reflect the latest info.
        cursor.execute(
            """
            INSERT OR IGNORE INTO scraped_data (ric, web_link, status)
            VALUES (?, ?, ?)
            """,
            (ric, about_url, status),
        )

        cursor.execute(
            """
            UPDATE scraped_data
            SET web_link = ?, status = ?
            WHERE ric = ?
            """,
            (about_url, status, ric),
        )

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error in save_to_db: {e}")
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

        data = read_xlsx(file)

        insert_data(data, conn)

    # Close the connection
    if conn:
        conn.close()
