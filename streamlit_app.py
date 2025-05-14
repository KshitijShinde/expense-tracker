import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import matplotlib.pyplot as plt
import io

# Initialize Firebase
from firebase_config import db  # Ensure this imports Firestore DB instance

st.title("Expense Tracker 📊")

# --- Input Form for "Money In" ---
st.subheader("Add Income")
with st.form("income_form"):
    income_date = st.date_input("Select Income Date")
    income_source = st.text_input("Income Source (e.g., Salary, Bonus)")
    income_amount = st.number_input("Enter Income Amount", min_value=0.0, format="%.2f")
    income_submitted = st.form_submit_button("Save Income")

if income_submitted:
    income_date_str = income_date.strftime('%Y-%m-%d')
    db.collection('income').add({
        'date': income_date_str,
        'source': income_source,
        'amount': income_amount
    })
    st.success(f"Added ₹{income_amount} income from {income_source} on {income_date_str}")

# --- Input Form to Add Expenses ---
st.subheader("Add Expense")
with st.form("expense_form"):
    date = st.date_input("Select Expense Date", key="expense_date")
    category = st.text_input("Expense Category", key="expense_category").strip().title()
    description = st.text_input("Description (e.g., Grocery at Walmart)", key="expense_desc")
    amount = st.number_input("Expense Amount", min_value=0.0, format="%.2f", key="expense_amount")
    submitted = st.form_submit_button("Save Expense")

if submitted:
    date_str = date.strftime('%Y-%m-%d')
    db.collection('expenses').add({
        'date': date_str,
        'category': category,
        'description': description,
        'amount': amount
    })
    st.success(f"Added ₹{amount} to {category} on {date_str} — {description}")

# --- Fetch Expenses ---
st.subheader("Current Expenses")
expenses_ref = db.collection('expenses')
expenses = expenses_ref.stream()
expense_data = [e.to_dict() for e in expenses]

# --- Fetch Income ---
income_ref = db.collection('income')
incomes = income_ref.stream()
income_data = [i.to_dict() for i in incomes]

# --- DataFrames ---
if expense_data:
    df_exp = pd.DataFrame(expense_data)
    st.dataframe(df_exp[["date", "category", "description", "amount"]].sort_values(by="date"))
else:
    df_exp = pd.DataFrame(columns=["date", "category", "description", "amount"])
    st.info("No expenses recorded yet.")

# --- Show Income Summary ---
if income_data:
    df_income = pd.DataFrame(income_data)
    total_income = df_income["amount"].sum()
else:
    df_income = pd.DataFrame(columns=["date", "source", "amount"])
    total_income = 0.0

# --- Calculate and Display Totals ---
total_expenses = df_exp["amount"].sum() if not df_exp.empty else 0.0
remaining_money = total_income - total_expenses

st.subheader("💰 Financial Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"₹{total_income:.2f}")
col2.metric("Total Expenses", f"₹{total_expenses:.2f}")
col3.metric("Money Remaining", f"₹{remaining_money:.2f}")

# --- Delete Expense ---
if not df_exp.empty:
    st.subheader("Delete an Expense")
    df_exp["display"] = df_exp["date"] + " | " + df_exp["category"] + " | " + df_exp["amount"].astype(str)
    expense_to_delete = st.selectbox("Select an Expense", df_exp["display"])
    if st.button("Delete Selected Expense"):
        parts = expense_to_delete.split(" | ")
        query = db.collection('expenses') \
                  .where('date', '==', parts[0]) \
                  .where('category', '==', parts[1]) \
                  .where('amount', '==', float(parts[2]))
        for doc in query.stream():
            db.collection('expenses').document(doc.id).delete()
        st.success(f"Deleted expense: {expense_to_delete}")

# --- Pie Chart ---
if not df_exp.empty:
    st.subheader("Expense Analytics (Pie Chart)")
    category_sums = df_exp.groupby("category")["amount"].sum().reset_index()
    plt.figure(figsize=(8, 8))
    plt.pie(category_sums['amount'], labels=category_sums['category'], autopct='%1.1f%%', startangle=90)
    plt.title("Expenses by Category")
    st.pyplot(plt)

# --- Download as Excel ---
def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')
    return output.getvalue()

if not df_exp.empty:
    excel_data = convert_df_to_excel(df_exp)
    st.download_button(
        label="📥 Download Expenses as Excel",
        data=excel_data,
        file_name='expenses.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
