import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

EXCEL_FILE = r"C:\Users\HP\OneDrive\Desktop\expenses.xlsx"

# --- Load or initialize Excel ---
if 'df' not in st.session_state:
    if os.path.exists(EXCEL_FILE):
        st.session_state.df = pd.read_excel(EXCEL_FILE)
    else:
        st.session_state.df = pd.DataFrame(columns=['Date'])  # start with Date column
        st.session_state.df.to_excel(EXCEL_FILE, index=False)

st.title("Expense Tracker 📊")

# --- Input Form (Moved to the Top) ---
with st.form("expense_form"):
    date = st.date_input("Select Date")
    category = st.text_input("Enter Category")
    amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Save Expense")

if submitted:
    date_str = date.strftime('%Y-%m-%d')
    
    df = st.session_state.df
    
    if category not in df.columns:
        df[category] = None
    
    if date_str in df['Date'].astype(str).values:
        current_amount = df.loc[df['Date'].astype(str) == date_str, category].values
        if current_amount.size > 0 and pd.notna(current_amount[0]):
            df.loc[df['Date'].astype(str) == date_str, category] += amount
        else:
            df.loc[df['Date'].astype(str) == date_str, category] = amount
    else:
        new_row = {col: None for col in df.columns}
        new_row['Date'] = date_str
        new_row[category] = amount
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    df = df.groupby('Date', as_index=False).sum()
    cols = ['Date'] + [col for col in df.columns if col != 'Date']
    df = df[cols]
    
    st.session_state.df = df  # Store updated df in session state
    df.to_excel(EXCEL_FILE, index=False)
    
    st.success(f"Added {amount} to {category} on {date_str}")
    st.experimental_rerun()

# --- Delete Expense Section ---
st.subheader("Delete Expense")

df = st.session_state.df

if len(df) > 0:
    delete_date = st.date_input("Select Date to Delete Expense", key='delete_date')
    delete_category = st.selectbox("Select Category to Delete", [col for col in df.columns if col != 'Date'])
    delete_button = st.button("Delete Expense")

    if delete_button:
        delete_date_str = delete_date.strftime('%Y-%m-%d')
        if delete_date_str in df['Date'].astype(str).values:
            df.loc[df['Date'].astype(str) == delete_date_str, delete_category] = None
            
            row_values = df.loc[df['Date'].astype(str) == delete_date_str, df.columns != 'Date']
            if row_values.isnull().all(axis=1).values[0]:
                df = df[df['Date'].astype(str) != delete_date_str]
                st.info(f"Deleted entire row for {delete_date_str} as all categories were empty.")
            else:
                st.success(f"Deleted {delete_category} expense on {delete_date_str}")
            
            st.session_state.df = df  # Store updated df in session state
            df.to_excel(EXCEL_FILE, index=False)
            st.experimental_rerun()
        else:
            st.warning(f"No record found for {delete_date_str}")

# --- Delete Entire Category Section ---
st.subheader("Delete Entire Category")

existing_categories = [col for col in df.columns if col != 'Date']
if existing_categories:
    selected_category_to_delete = st.selectbox("Select Category to Delete Permanently", existing_categories, key='delete_category')
    delete_category_button = st.button("Delete Entire Category")

    if delete_category_button:
        df.drop(columns=[selected_category_to_delete], inplace=True)
        st.session_state.df = df  # Store updated df in session state
        df.to_excel(EXCEL_FILE, index=False)
        st.success(f"Category '{selected_category_to_delete}' has been permanently deleted.")
        st.experimental_rerun()
else:
    st.info("No categories available to delete.")

# --- Show current table ---
st.subheader("Current Expenses")

if len(df) > 0:
    category_cols = [col for col in df.columns if col != 'Date']
    totals = {col: df[col].sum(skipna=True) for col in category_cols}
    total_row = {'Date': 'Total'}
    total_row.update(totals)
    df_display = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
else:
    df_display = df

df_display['Date'] = pd.to_datetime(df_display['Date'], errors='coerce')
df_display = df_display.sort_values(by='Date', ascending=True).reset_index(drop=True)

cols = ['Date'] + [col for col in df_display.columns if col != 'Date']
df_display = df_display[cols]

st.dataframe(df_display.fillna(""))

# --- Analytics Graph: Expense per Category (Pie Chart) ---
st.subheader("Expense Analytics (Pie Chart)")

if len(df) > 0:
    category_sums = {col: df[col].sum(skipna=True) for col in df.columns if col != 'Date'}
    category_df = pd.DataFrame(list(category_sums.items()), columns=['Category', 'Total Expense'])
    plt.figure(figsize=(8, 8))
    plt.pie(category_df['Total Expense'], labels=category_df['Category'], autopct='%1.1f%%', startangle=90)
    plt.title("Expenses by Category")
    st.pyplot(plt)
