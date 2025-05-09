import streamlit as st
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Connect to PostgreSQL using Streamlit Secrets ---

# Retrieve environment variables
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT'))  # Convert to integer
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Attempt to connect to the PostgreSQL database with SSL enabled
try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode='require'  # Ensure SSL is used
    )
    print("Connected successfully")
except psycopg2.OperationalError as e:
    print(f"Error: {e}")
    st.error(f"Error: {e}")  # Display the error message on the Streamlit UI
    conn = None  # Set conn to None to avoid further code execution

# If the connection is successful, proceed with the rest of the code
if conn:
    # Initialize cursor
    cursor = conn.cursor()

    # --- Setup Database Table (Create if Not Exists) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id SERIAL PRIMARY KEY,
        date DATE,
        category TEXT,
        amount NUMERIC
    );
    """)
    conn.commit()

    # Streamlit app title
    st.title("Expense Tracker 📊")

    # --- Input Form (to add new expenses) ---
    with st.form("expense_form"):
        date = st.date_input("Select Date")
        category = st.text_input("Enter Category")
        amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Save Expense")

    if submitted:
        date_str = date.strftime('%Y-%m-%d')
        
        # Insert the expense into the database
        cursor.execute("""
        INSERT INTO expenses (date, category, amount)
        VALUES (%s, %s, %s)
        """, (date_str, category, amount))
        conn.commit()
        
        st.success(f"Added {amount} to {category} on {date_str}")

    # --- Show Current Expenses in DataFrame ---
    st.subheader("Current Expenses")

    cursor.execute("SELECT * FROM expenses ORDER BY date ASC")
    data = cursor.fetchall()

    if data:
        df = pd.DataFrame(data, columns=["ID", "Date", "Category", "Amount"])
        df = df.drop(columns=["ID"])  # Remove ID column

        # Pivot the data: Date as rows, Category as columns, and Amount as values
        df_pivoted = df.pivot_table(index="Date", columns="Category", values="Amount", aggfunc="sum", fill_value=0)

        # Add a total row at the bottom
        df_pivoted.loc["Total"] = df_pivoted.sum(axis=0)
        
        st.dataframe(df_pivoted)

        # --- Option to delete an expense ---
        st.subheader("Delete an Expense")
        expense_to_delete = st.selectbox("Select an Expense to Delete", df['Date'] + " | " + df['Category'] + " | " + df['Amount'].astype(str))
        
        if st.button("Delete Selected Expense"):
            # Extract date, category, and amount from selected item
            date_category_amount = expense_to_delete.split(" | ")
            date_to_delete = date_category_amount[0]
            category_to_delete = date_category_amount[1]
            amount_to_delete = float(date_category_amount[2])

            # Delete the selected expense from the database
            cursor.execute("""
            DELETE FROM expenses WHERE date = %s AND category = %s AND amount = %s
            """, (date_to_delete, category_to_delete, amount_to_delete))
            conn.commit()
            
            st.success(f"Deleted expense: {expense_to_delete}")
    else:
        st.info("No expenses to display.")

    # --- Analytics Graph: Expenses by Category (Pie Chart) ---
    st.subheader("Expense Analytics (Pie Chart)")

    if data:
        df = pd.DataFrame(data, columns=["ID", "Date", "Category", "Amount"])
        category_sums = df.groupby("Category")["Amount"].sum().reset_index()
        
        plt.figure(figsize=(8, 8))
        plt.pie(category_sums['Amount'], labels=category_sums['Category'], autopct='%1.1f%%', startangle=90)
        plt.title("Expenses by Category")
        st.pyplot(plt)

else:
    st.error("Failed to connect to the database. Please check your connection settings.")
