from src.connections.oracle_connection import get_oracle_connection


def main():
    connection = get_oracle_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT COUNT(*)
                FROM MB_CUSTOMERS
            """)

            row_count = cursor.fetchone()[0]

            print("Connected to Oracle successfully.")
            print(f"Oracle user: MIGRATION_USER")
            print(f"MB_CUSTOMERS row count: {row_count}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()