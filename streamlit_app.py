import streamlit as st
import pandas as pd
import sqlite3
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --- Setup SQLite Database ---
DB_FILE = "expenses.db"

# Initialize connection
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    category TEXT,
    amount REAL
)
""")
conn.commit()

st.title("Expense Tracker 📊")

# --- Input Form (Moved to the Top) ---
with st.form("expense_form"):
    date = st.date_input("Select Date")
    category = st.text_input("Enter Category")
    amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Save Expense")

if submitted:
    date_str = date.strftime('%Y-%m-%d')
    
    # Insert expense into the database
    cursor.execute("""
    INSERT INTO expenses (date, category, amount)
    VALUES (?, ?, ?)
    """, (date_str, category, amount))
    conn.commit()
    
    st.success(f"Added {amount} to {category} on {date_str}")
    st.experimental_rerun()

# --- Delete Expense Section ---
st.subheader("Delete Expense")

# Fetch all expenses for selection
cursor.execute("SELECT DISTINCT date FROM expenses")
dates = [row[0] for row in cursor.fetchall()]

if dates:
    delete_date = st.date_input("Select Date to Delete Expense", key='delete_date')
    delete_category = st.selectbox("Select Category to Delete", ["All Categories"] + [row[0] for row in cursor.execute("SELECT DISTINCT category FROM expenses")])
    delete_button = st.button("Delete Expense")

    if delete_button:
        delete_date_str = delete_date.strftime('%Y-%m-%d')
        if delete_category == "All Categories":
            cursor.execute("DELETE FROM expenses WHERE date = ?", (delete_date_str,))
        else:
            cursor.execute("DELETE FROM expenses WHERE date = ? AND category = ?", (delete_date_str, delete_category))
        conn.commit()
        
        st.success(f"Deleted expense for {delete_category} on {delete_date_str}")
        st.experimental_rerun()

# --- Delete Entire Category Section ---
st.subheader("Delete Entire Category")

# List all categories
cursor.execute("SELECT DISTINCT category FROM expenses")
categories = [row[0] for row in cursor.fetchall()]

if categories:
    selected_category_to_delete = st.selectbox("Select Category to Delete Permanently", categories, key='delete_category')
    delete_category_button = st.button("Delete Entire Category")

    if delete_category_button:
        cursor.execute("DELETE FROM expenses WHERE category = ?", (selected_category_to_delete,))
        conn.commit()
        st.success(f"Category '{selected_category_to_delete}' has been permanently deleted.")
        st.experimental_rerun()
else:
    st.info("No categories available to delete.")

# --- Show current table ---
st.subheader("Current Expenses")

cursor.execute("SELECT * FROM expenses ORDER BY date ASC")
data = cursor.fetchall()

# Display the data
if data:
    df = pd.DataFrame(data, columns=["ID", "Date", "Category", "Amount"])
    st.dataframe(df.drop(columns=["ID"]))
else:
    st.info("No expenses to display.")

# --- Analytics Graph: Expense per Category (Pie Chart) ---
st.subheader("Expense Analytics (Pie Chart)")

if data:
    df = pd.DataFrame(data, columns=["ID", "Date", "Category", "Amount"])
    category_sums = df.groupby("Category")["Amount"].sum().reset_index()
    
    plt.figure(figsize=(8, 8))
    plt.pie(category_sums['Amount'], labels=category_sums['Category'], autopct='%1.1f%%', startangle=90)
    plt.title("Expenses by Category")
    st.pyplot(plt)
