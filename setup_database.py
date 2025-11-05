import mysql.connector
import os
import hashlib
from dotenv import load_dotenv
from pathlib import Path

# ✅ Load .env file from the same folder as the script
load_dotenv(dotenv_path=Path(__file__).parent / ".env")





# ============================================================
# Step 1: Take MySQL credentials interactively or from env vars
# ============================================================
def get_sql_credentials():
    """Prompt user for MySQL credentials (or use existing environment values)."""
    host = input(f"MySQL Host [{os.getenv('DB_HOST', '127.0.0.1')}]: ") or os.getenv('DB_HOST', '127.0.0.1')
    user = input(f"MySQL Username [{os.getenv('DB_USER', 'root')}]: ") or os.getenv('DB_USER', 'root')
    password = input("MySQL Password (leave blank if none): ") or os.getenv('DB_PASSWORD', '')
    db_name = input(f"Database Name [{os.getenv('DB_NAME', 'clientquery_db')}]: ") or os.getenv('DB_NAME', 'clientquery_db')

    # Save to environment variables
    os.environ["DB_HOST"] = host
    os.environ["DB_USER"] = user
    os.environ["DB_PASSWORD"] = password
    os.environ["DB_NAME"] = db_name

    return host, user, password, db_name


# ============================================================
# Step 2: Connect to MySQL (no DB selected — used during setup)
# ============================================================
def get_root_connection():
    """Connect to MySQL server without selecting a specific database."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


# ============================================================
# Step 3: Connect to MySQL (with DB selected — used after setup)
# ============================================================
def get_connection():
    """Connect to the selected database if it exists."""
    #db_name = os.getenv("DB_NAME")
    #if not db_name:
        #raise ValueError("❌ No database name found in environment variables. Run setup_database.py first.")
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")  # ✅ ensures connection is tied to DB
    )
     
    

# ============================================================
# Step 4: Create Database and Tables if not exist
# ============================================================
def setup_database():
    """Create the database and required tables."""
    host, user, password, db_name = get_sql_credentials()

    print(f"\n🔧 Connecting to MySQL server at {host}...")
    conn = get_root_connection()
    cursor = conn.cursor()

    # Create database if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    cursor.execute(f"USE {db_name}")

    print(f"✅ Database '{db_name}' is ready.")

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role ENUM('Client', 'Support') DEFAULT 'Client'
        )
    """)

    # Create client_queries table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS client_queries (
            query_id VARCHAR(10) PRIMARY KEY,
            client_email VARCHAR(255),
            client_mobile VARCHAR(20),
            query_heading VARCHAR(255),
            query_description TEXT,
            status ENUM('Open', 'Closed') DEFAULT 'Open',
            query_created_time DATETIME DEFAULT NOW(),
            query_closed_time DATETIME NULL
        )
    """)
    # ============================================================
    # Create Trigger for Auto-Generating Query IDs
    # ============================================================
    try:
     cursor.execute("DROP TRIGGER IF EXISTS before_insert_client_queries")
     cursor.execute("""
        CREATE TRIGGER before_insert_client_queries
        BEFORE INSERT ON client_queries
        FOR EACH ROW
        BEGIN
            DECLARE next_id INT;

            -- Generate next query_id only if not manually provided
            IF NEW.query_id IS NULL OR NEW.query_id = '' THEN
                SELECT 
                    COALESCE(
                        CAST(SUBSTRING(query_id, 2) AS UNSIGNED), 
                        0
                    ) + 1 
                INTO next_id
                FROM client_queries
                ORDER BY query_id DESC
                LIMIT 1;

                SET NEW.query_id = CONCAT('Q', LPAD(next_id, 4, '0'));
            END IF;
        END
         """)
     print("✅ Trigger 'before_insert_client_queries' created successfully!")
    except Exception as e:
      print(f"⚠️ Failed to create trigger: {e}")


    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Tables created successfully!")


# ============================================================
# Step 5: Save credentials to .env file
# ============================================================
def save_env():
    """Save MySQL credentials to .env for reuse"""
    env_content = f"""DB_HOST={os.getenv('DB_HOST')}
DB_USER={os.getenv('DB_USER')}
DB_PASSWORD={os.getenv('DB_PASSWORD')}
DB_NAME={os.getenv('DB_NAME')}
"""
    with open(".env", "w") as f:
        f.write(env_content)
    print("💾 Credentials saved to .env successfully.")


# ============================================================
# Step 6: Hash Password
# ============================================================
def hash_password(password):
    """Hash passwords using SHA-256 (consistent with app.py)."""
    return hashlib.sha256(password.encode()).hexdigest()


# ============================================================
# Step 6: Optional - Seed dummy data
# ============================================================

def seed_dummy_data():
    """Insert sample users and queries for testing."""
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )
    cursor = conn.cursor()

    # Hash dummy passwords properly
    alice_pw = hash_password("alice123")
    bob_pw = hash_password("bob123")
    supp_pw = hash_password("support123")

    cursor.execute("""
        INSERT IGNORE INTO users (username, hashed_password, role)
        VALUES 
        (%s, %s, %s),
        (%s, %s, %s),
        (%s, %s, %s)
    """, (
        "Alice", alice_pw, "Client",
        "Bob", bob_pw, "Client",
        "SUPP0001", supp_pw, "Support"
    ))

    conn.commit()
    cursor.close()
    conn.close()

    print("🌱 Dummy data seeded successfully with hashed passwords!")


# ============================================================
# Step 7: Run setup
# ============================================================
if __name__ == "__main__":
    print("🔧 Setting up portable Client Query Management database...\n")
    setup_database()
    save_env()

    choice = input("\nWould you like to seed dummy users data for testing? (y/n): ").lower()
    if choice == "y":
        seed_dummy_data()

    print("\n🎉 Setup complete!")
