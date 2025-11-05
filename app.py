import streamlit as st
import mysql.connector
import pandas as pd
import hashlib
import matplotlib.pyplot as plt
from datetime import datetime
from setup_database import get_connection
from setup_database import hash_password
from dotenv import load_dotenv
from pathlib import Path

# ✅ Load .env file from the same folder as the script
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


# ======================
# USER REGISTRATION
# ======================
def register_user(username, password, role):
    conn = get_connection()
    cursor = conn.cursor()

    # Check for pre existing user names
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (username,))
    exists = cursor.fetchone()[0]

    if exists:
        cursor.close()
        conn.close()
        return False

    # Use your existing hash_password() function
    hashed_pw = hash_password(password)

    cursor.execute(
        "INSERT INTO users (username, hashed_password, role) VALUES (%s,%s, %s)",
        (username, hashed_pw, role)
    )

    conn.commit()
    cursor.close()
    conn.close()
    return True


# ======================
# LOGIN FUNCTION
# ======================
def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Hash the entered password
    hashed_pw = hash_password(password)

    # Check credentials from the unified users table
    cursor.execute(
        "SELECT * FROM users WHERE username = %s AND hashed_password = %s",
        (username, hashed_pw)
    )
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    # If user found, extract role from DB
    if user:
        role = user.get("role", "Client")  # Default to 'Client' if missing
        return user, role
    else:
        return None, None


# ======================
# STREAMLIT SETUP
# ======================
st.set_page_config(page_title="Client Query Management System", page_icon="📋")
st.title("📋 Client Query Management System")

menu = ["Login","Register"]
choice = st.sidebar.radio("Select Action", menu)

# ======================
# CLIENT REGISTER
# ======================
if choice == "Register":
    st.subheader("🧾 Register")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Select Role", ["Client", "Support"])

    if st.button("Register"):
        try:
         success = register_user(username, password, role)
         if success:
            st.success("✅ Registration successful! Please log in.")
         else:
            st.warning(f"⚠️ Username '{username}' already exists. Please choose another.")
        except Exception as e:
            st.error(f"❌ Error: {e}")

# ======================
# LOGIN HANDLING
# ======================
elif choice == "Login":
    # If not logged in yet
    if "role" not in st.session_state:
        st.subheader("🔐 Login Portal")
        username = st.text_input("Username (e.g., John123 or SUPP0123)")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user, role = login_user(username, password)
            if user:
                st.session_state["username"] = username
                st.session_state["role"] = role
                st.success(f"✅ Logged in as {role}: {username}")
                st.rerun() 
            else:
                st.error("❌ Invalid username or password")

    # ======================
    # CLIENT DASHBOARD
    # ======================
    elif st.session_state["role"] == "Client":
        st.subheader(f"📩 Welcome {st.session_state['username']}")
        st.markdown("### Submit a New Query")

        email = st.text_input("Email ID")
        mobile = st.text_input("Mobile Number")
        heading = st.text_input("Query Heading")
        description = st.text_area("Query Description")

        if st.button("Submit Query"):
            try:
                conn = get_connection()
                cursor = conn.cursor()

                # Generate query_id like Q0001
                cursor.execute("SELECT COUNT(*) FROM client_queries")
                count = cursor.fetchone()[0] + 1
                query_id = f"Q{count:04d}"

                cursor.execute("""
                    INSERT INTO client_queries 
                    (query_id, client_email, client_mobile, query_heading, query_description, status, query_created_time)
                    VALUES (%s, %s, %s, %s, %s, 'Open', %s)
                """, (query_id, email, mobile, heading, description, datetime.now()))
                conn.commit()
                cursor.close()
                conn.close()
                st.success(f"✅ Query {query_id} submitted successfully!")
            except Exception as e:
                st.error(f"⚠️ Error: {e}")

    # ======================
    # SUPPORT DASHBOARD + ANALYTICS (TABS)
    # ======================
    elif st.session_state["role"] == "Support":
        st.markdown(f"✅ Logged in as **Support:** {st.session_state['username']}")
        tab1, tab2 = st.tabs(["🧰 Support Dashboard", "📈 Support Analytics"])

        # -------- Support Dashboard --------
        with tab1:
            st.subheader("🛠️ Support Dashboard")
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM client_queries")
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=cols)
                cursor.close()
                conn.close()

                # Display all queries
                st.dataframe(df)

                # Filter section
                st.markdown("### 🔍 Filter Queries")

                # Dropdown filters
                col1, col2 = st.columns(2)

                with col1:
                 status_filter = st.selectbox("Filter by Status", ["All", "Open", "Closed"])

                with col2:
                  query_headings = df["query_heading"].dropna().unique().tolist()
                  query_headings.sort()
                  heading_filter = st.selectbox("Filter by Query Heading", ["All"] + query_headings)

                # Apply filters
                filtered_df = df.copy()

                if status_filter != "All":
                 filtered_df = filtered_df[filtered_df["status"].str.lower() == status_filter.lower()]

                if heading_filter != "All":
                 filtered_df = filtered_df[filtered_df["query_heading"].str.lower() == heading_filter.lower()]

               # Show filtered results
                st.markdown("### 📋 Filtered Results")
                if not filtered_df.empty:
                 st.dataframe(filtered_df)
                else:
                 st.warning("⚠️ No matching results found.")


                # Close query section
                st.markdown("### ✅ Close a Query")
                query_id = st.text_input("Enter Query ID to close:")
                if st.button("Close Query"):
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE client_queries SET status='Closed', query_closed_time=%s WHERE query_id=%s",
                        (datetime.now(), query_id)
                    )
                    conn.commit()
                    cursor.close()
                    conn.close()
                    st.success(f"✅ Query {query_id} marked as Closed!")

            except Exception as e:
                st.error(f"⚠️ Error loading dashboard: {e}")

        # -------- Support Analytics --------
        with tab2:
            st.subheader("📊 Support Performance Analytics")
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM client_queries")
                rows = cursor.fetchall()
                cols = [desc[0] for desc in cursor.description]
                df = pd.DataFrame(rows, columns=cols)
                cursor.close()
                conn.close()

                # Convert to datetime
                df["query_created_time"] = pd.to_datetime(df["query_created_time"], errors="coerce")
                df["query_closed_time"] = pd.to_datetime(df["query_closed_time"], errors="coerce")

                total_queries = len(df)
                open_queries = len(df[df["status"] == "Open"])
                closed_queries = len(df[df["status"] == "Closed"])

                st.metric("Total Queries", total_queries)
                st.metric("Open Queries", open_queries)
                st.metric("Closed Queries", closed_queries)

                # Average resolution time
                df_closed = df.dropna(subset=["query_closed_time"])
                if not df_closed.empty:
                    df_closed["resolution_time"] = (df_closed["query_closed_time"] - df_closed["query_created_time"]).dt.total_seconds() / 3600
                    avg_res = df_closed["resolution_time"].mean()
                    st.metric("Average Resolution Time (hrs)", f"{avg_res:.2f}")

                # Query trend over time
                try:
                 df["query_created_time"] = pd.to_datetime(df["query_created_time"], errors="coerce")
                 df_trend = df.dropna(subset=["query_created_time"])
                 daily_trend = df_trend.groupby(df_trend["query_created_time"].dt.date).size().reset_index(name="count")

                 fig, ax = plt.subplots(figsize=(8, 3))
                 ax.plot(daily_trend["query_created_time"], daily_trend["count"], marker="o", color="#0072B2")
                 ax.set_title("📈 Daily Query Creation Trend", fontsize=12, fontweight="bold")
                 ax.set_xlabel("Date", fontsize=10)
                 ax.set_ylabel("Number of Queries", fontsize=10)
                 ax.grid(True, linestyle="--", alpha=0.6)
                 st.pyplot(fig)

                except Exception as e:
                 st.error(f"⚠️ Error loading analytics (Query Trend): {e}")

                # --- Support Load Trend ---
                st.markdown("### 💼 Support Load Trend (Open Queries Over Time)")
                try:
                 open_df = df[df["status"].str.lower() == "open"]
                 open_df["query_created_time"] = pd.to_datetime(open_df["query_created_time"], errors="coerce")

                 load_trend = open_df.groupby(open_df["query_created_time"].dt.date).size().reset_index(name="open_queries")

                 fig3, ax3 = plt.subplots(figsize=(8, 3))
                 ax3.plot(load_trend["query_created_time"], load_trend["open_queries"], color="#E69F00", marker="o")
                 ax3.set_title("Support Load (Open Queries Over Time)", fontsize=12, fontweight="bold")
                 ax3.set_xlabel("Date", fontsize=10)
                 ax3.set_ylabel("Open Queries", fontsize=10)
                 ax3.grid(True, linestyle="--", alpha=0.6)
                 st.pyplot(fig3)

                except Exception as e:
                 st.error(f"⚠️ Error loading support load trend: {e}")

                # --- Category wise count Bar chart
                st.markdown("### 📊 Query Count by Heading")

                try:
                 # Add a unique key to avoid conflicts with other selectboxes
                 status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Open", "Closed"],
                key="bar_chart_status_filter"
                )

                 # Filter data based on selection
                 filtered_df = df.copy()
                 if status_filter != "All":
                  filtered_df = filtered_df[filtered_df["status"].str.lower() == status_filter.lower()]

                 # Group by heading and count
                 heading_counts = (
                 filtered_df.groupby("query_heading")
                 .size()
                 .reset_index(name="query_count")
                 .sort_values("query_count", ascending=False)
                  )

                 if heading_counts.empty:
                  st.warning("⚠️ No data available for the selected filter.")
                 else:
                  import matplotlib.pyplot as plt
                  fig, ax = plt.subplots(figsize=(8, 4))
                  ax.barh(heading_counts["query_heading"], heading_counts["query_count"], color="#0072B2")
                  ax.set_xlabel("Number of Queries")
                  ax.set_ylabel("Query Heading")
                  ax.set_title(f"Query Count by Heading ({status_filter})", fontsize=12, fontweight="bold")
                  ax.grid(True, linestyle="--", alpha=0.5)
                  ax.invert_yaxis()
                  st.pyplot(fig)

                except Exception as e:
                 st.error(f"⚠️ Error loading Query Heading chart: {e}")



            except Exception as e:
                st.error(f"⚠️ Error loading analytics: {e}")


   