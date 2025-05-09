import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Initialize Firebase
import firebase_config  # This will initialize Firebase with firebase_credentials.json
db = firebase_config.db

# Streamlit app title
st.title("Expense Tracker 📊")

# --- Input Form (to add new expenses) ---
with st.form("expense_form"):
    date = st.date_input("Select Date")
    category = st.text_input("Enter Category")
    amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Save Expense")

if submitted:
    # Convert date to string format to store in Firebase
    date_str = date.strftime('%Y-%m-%d')
    
    # Store the expense in Firestore
    expense_ref = db.collection('expenses')
    expense_ref.add({
        'date': date_str,
        'category': category,
        'amount': amount
    })
    
    st.success(f"Added {amount} to {category} on {date_str}")

# --- Show Current Expenses in DataFrame ---
st.subheader("Current Expenses")

# Retrieve expenses from Firebase
expenses_ref = db.collection('expenses')
expenses = expenses_ref.stream()

# Create a list to hold expenses
expense_data = []
for expense in expenses:
    expense_data.append(expense.to_dict())

if expense_data:
    df = pd.DataFrame(expense_data)
    
    # Pivot the data: Date as rows, Category as columns, and Amount as values
    df_pivoted = df.pivot_table(index="date", columns="category", values="amount", aggfunc="sum", fill_value=0)

    # Add a total row at the bottom
    df_pivoted.loc["Total"] = df_pivoted.sum(axis=0)
    
    st.dataframe(df_pivoted)

    # --- Option to delete an expense ---
    st.subheader("Delete an Expense")
    expense_to_delete = st.selectbox("Select an Expense to Delete", df['date'] + " | " + df['category'] + " | " + df['amount'].astype(str))
    
    if st.button("Delete Selected Expense"):
        # Extract date, category, and amount from selected item
        date_category_amount = expense_to_delete.split(" | ")
        date_to_delete = date_category_amount[0]
        category_to_delete = date_category_amount[1]
        amount_to_delete = float(date_category_amount[2])

        # Delete the selected expense from Firebase
        query = db.collection('expenses').where('date', '==', date_to_delete).where('category', '==', category_to_delete).where('amount', '==', amount_to_delete)
        expense_to_delete_doc = query.stream()

        # Delete the document(s) from Firebase
        for doc in expense_to_delete_doc:
            db.collection('expenses').document(doc.id).delete()
        
        st.success(f"Deleted expense: {expense_to_delete}")
else:
    st.info("No expenses to display.")

# --- Analytics Graph: Expenses by Category (Pie Chart) ---
st.subheader("Expense Analytics (Pie Chart)")

if expense_data:
    df = pd.DataFrame(expense_data)
    category_sums = df.groupby("category")["amount"].sum().reset_index()
    
    # Create a pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(category_sums['amount'], labels=category_sums['category'], autopct='%1.1f%%', startangle=90)
    plt.title("Expenses by Category")
    st.pyplot(plt)
