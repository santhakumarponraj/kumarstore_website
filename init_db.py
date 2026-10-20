import os
import sys
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "Admin@123")
DB_NAME = os.getenv("DB_NAME", "kumarstore_db")

def init_database():
    print(f"Connecting to MySQL server at {DB_HOST}:{DB_PORT} as {DB_USER}...")
    
    # First ensure database exists
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        charset='utf8mb4',
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
    )
    
    try:
        with conn.cursor() as cursor:
            print(f"Ensuring database `{DB_NAME}` exists...")
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.commit()
    finally:
        conn.close()

    # Now connect with the database selected
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4',
        client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(base_dir, "schema.sql")
    seed_path = os.path.join(base_dir, "seed.sql")

    try:
        with conn.cursor() as cursor:
            print("Executing schema.sql...")
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            cursor.execute(schema_sql)
            conn.commit()
            print("Schema created successfully!")

            print("Executing seed.sql...")
            with open(seed_path, "r", encoding="utf-8") as f:
                seed_sql = f.read()
            cursor.execute(seed_sql)
            conn.commit()
            print("Seed data inserted successfully!")

            # Quick verification
            cursor.execute("SELECT COUNT(*) FROM categories;")
            cat_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM products;")
            prod_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM product_units;")
            unit_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]

            print(f"\nVerification Summary:")
            print(f"- Categories: {cat_count} (Mandatory 10)")
            print(f"- Products:   {prod_count}")
            print(f"- Unit Variants: {unit_count}")
            print(f"- Users:      {user_count}")

    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        conn.rollback()
        raise e
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
