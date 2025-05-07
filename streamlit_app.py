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

# --- Show Current Table ---
st.subheader("Current Expenses")

cursor.execute("SELECT * FROM expenses ORDER BY date ASC")
data = cursor.fetchall()

# Display the data in a pivot table format
if data:
    df = pd.DataFrame(data, columns=["ID", "Date", "Category", "Amount"])
    df = df.drop(columns=["ID"])  # Remove ID column
    
    # Pivot the data: Date as rows, Category as columns, and Amount as values
    df_pivoted = df.pivot_table(index="Date", columns="Category", values="Amount", aggfunc="sum", fill_value=0)

    # Add a total row at the bottom
    df_pivoted.loc["Total"] = df_pivoted.sum(axis=0)
    
    # Display the pivoted data with the total row
    st.dataframe(df_pivoted)
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
