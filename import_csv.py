import os
import pandas as pd
from setup_database import get_connection  # ✅ Reuse DB connection function
from dotenv import load_dotenv
from pathlib import Path

# ✅ Load .env file from the same folder as the script
load_dotenv(dotenv_path=Path(__file__).parent / ".env")




# ============================================================
# Step 1️⃣: Import CSV data dynamically
# ============================================================
def import_csv_to_db(csv_path=None):
    """Import query data from a CSV into the MySQL database."""

    # Default file
    if not csv_path:
        csv_path = "client_data.csv"

    # Ask user for file path if not found
    if not os.path.exists(csv_path):
        print(f"⚠️ Default file '{csv_path}' not found.")
        user_input = input("📁 Please enter the full path to your CSV file: ").strip()
        if not os.path.exists(user_input):
            print("❌ The file you entered does not exist. Exiting.")
            return
        csv_path = user_input

    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("✅ Connected to MySQL Database")

        # Load CSV
        df = pd.read_csv(csv_path)
        print(f"📄 Loaded CSV: {csv_path} ({len(df)} rows)")

        # Rename old columns (if applicable)
        df.rename(columns={
            "date_raised": "query_created_time",
            "date_closed": "query_closed_time"
        }, inplace=True)

        # Rename Opened with open
        df["status"] = df["status"].replace({"Opened": "Open"})


        # Convert to datetime safely
        df["query_created_time"] = pd.to_datetime(df["query_created_time"], errors="coerce")
        df["query_closed_time"] = pd.to_datetime(df["query_closed_time"], errors="coerce")

        # Replace NaT with None for SQL NULL
        df["query_closed_time"] = df["query_closed_time"].where(df["query_closed_time"].notna(), None)

        # SQL Insert Statement
        insert_query = """
            INSERT INTO client_queries (
                query_id,
                client_email,
                client_mobile,
                query_heading,
                query_description,
                status,
                query_created_time,
                query_closed_time
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        success, fail = 0, 0

        for i, row in df.iterrows():
            try:
                cursor.execute(insert_query, (
                    row["query_id"],
                    row["client_email"],
                    row["client_mobile"],
                    row["query_heading"],
                    row["query_description"],
                    row.get("status", "Open"),
                    row.get("query_created_time", None),
                    row.get("query_closed_time", None)
                ))
                success += 1
            except Exception as e:
                print(f"⚠️ Row {i+1} skipped due to error: {e}")#
                fail += 1

        conn.commit()
        print(f"✅ {success} rows inserted successfully! ⚠️ {fail} rows failed.")

    except FileNotFoundError:
        print("❌ CSV file not found! Please ensure client_data.csv exists.")
    except Exception as e:
        print(f"⚠️ Unexpected Error: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        print("🔒 MySQL connection closed.")

# ============================================================
# Step 2️⃣: Run Import
# ============================================================
if __name__ == "__main__":
    print("📦 Importing CSV data into client_query_db ...")
    import_csv_to_db()


