# 📋 Client Query Management System (Streamlit + MySQL)

A complete Streamlit-based web dashboard for managing and tracking client queries with real-time updates, analytics, and user role management.

---

## 🚀 Features

✅ Easy MySQL setup — automatic database and table creation  
✅ Client & Support role-based dashboards  
✅ Live query intake through Streamlit forms  
✅ Real-time status updates (Open / Closed)  
✅ Query analytics and trend visualization  
✅ CSV import support for bulk data  
✅ Secure password hashing (SHA-256)  
✅ Dummy data seeding for quick testing  
✅ Portable configuration via `.env`

---

## 🏗️ Project Structure
```
ClientQueryManagement/
│
├── app.py → Streamlit dashboard (main app)
├── setup_database.py → Creates DB, tables, dummy users
├── import_csv.py → Imports queries from CSV
├── client_data.csv → Sample dataset 
├── .env → MySQL credentials (auto-generated)
├── requirements.txt → Python dependencies
└── venv/ → Virtual environment (excluded from repo)

```



---

## ⚙️ Setup Instructions

 1️⃣ Clone the repository
```bash
git clone https://github.com/praneshrams07/ClientQueryManagement.git
cd ClientQueryManagement
```

2️⃣ Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate    # Mac/Linux
venv\Scripts\activate       # Windows 
```

3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

4️⃣ Run the setup script
```bash
python setup_database.py
```
- Creates the MySQL database and tables
- Saves credentials to .env
- Optionally seeds dummy users for testing

5️⃣ Import CSV data 
```bash
python import_csv.py
```

6️⃣ Launch the Streamlit dashboard
```bash
streamlit run app.py
```

👥 Default Dummy Users

| Username | Password   | Role     |
|-----------|------------|----------|
| Alice     | alice123   | Client   |
| Bob       | bob123     | Client   |
| SUPP0001  | support123 | Support  |


## 🧠 Built With

- Python 3.12  
- Streamlit for UI  
- MySQL for database  
- Pandas for data handling  
- Matplotlib for visualizations  
- Python-dotenv for environment management  


🏁 Author

**Praneshram S**
