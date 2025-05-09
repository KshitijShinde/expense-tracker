import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns

# --- PostgreSQL Connection Settings (from Streamlit secrets) ---
DB_HOST = st.secrets["DB_HOST"]
DB_PORT = st.secrets["DB_PORT"]
DB_NAME = st.secrets["DB_NAME"]
DB_USER = st.secrets["DB_USER"]
DB_PASSWORD = st.secrets["DB_PASSWORD"]

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

# --- Create Table if Not Exists ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    date DATE,
    category TEXT,
    amount NUMERIC
)
""")
conn.commit()

st.title("Expense Tracker 📊")

# --- Input Form ---
with st.form("expense_form"):
    date = st.date_input("Select Date")
    category = st.text_input("Enter Category")
    amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Save Expense")

if submitted:
    date_str = date.strftime('%Y-%m-%d')
    cursor.execute("""
    INSERT INTO expenses (date, category, amount)
    VALUES (%s, %s, %s)
    """, (date_str, category, amount))
    conn.commit()
    st.success(f"Added {amount} to {category} on {date_str}")

# --- Show Current Table ---
st.subheader("Current Expenses")
cursor.execute("SELECT id, date, category, amount FROM expenses ORDER BY date ASC")
data = cursor.fetchall()

if data:
    df = pd.DataFrame(data, columns=["ID", "Date", "Category", "Amount"])
    df_display = df.drop(columns=["ID"])

    df_pivoted = df_display.pivot_table(index="Date", columns="Category", values="Amount", aggfunc="sum", fill_value=0)
    df_pivoted.loc["Total"] = df_pivoted.sum(axis=0)
    st.dataframe(df_pivoted)

    # Delete expense
    st.subheader("Delete an Expense")
    df['Display'] = df['Date'].astype(str) + " | " + df['Category'] + " | " + df['Amount'].astype(str)
    expense_to_delete = st.selectbox("Select an Expense to Delete", df['Display'])

    if st.button("Delete Selected Expense"):
        selected_row = df[df['Display'] == expense_to_delete].iloc[0]
        cursor.execute("DELETE FROM expenses WHERE id = %s", (selected_row['ID'],))
        conn.commit()
        st.success(f"Deleted expense {expense_to_delete}")
else:
    st.info("No expenses to display.")

# --- Analytics Graph ---
st.subheader("Expense Analytics (Pie Chart)")

if data:
    category_sums = df.groupby("Category")["Amount"].sum().reset_index()
    plt.figure(figsize=(8, 8))
    plt.pie(category_sums['Amount'], labels=category_sums['Category'], autopct='%1.1f%%', startangle=90)
    plt.title("Expenses by Category")
    st.pyplot(plt)
