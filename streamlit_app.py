import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

EXCEL_FILE = r"C:\Users\HP\OneDrive\Desktop\expenses.xlsx"

# --- Load or initialize Excel ---
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
else:
    df = pd.DataFrame(columns=['Date'])  # start with Date column
    df.to_excel(EXCEL_FILE, index=False)

st.title("Expense Tracker 📊")

# --- Input Form (Moved to the Top) ---
with st.form("expense_form"):
    date = st.date_input("Select Date")
    category = st.text_input("Enter Category")
    amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Save Expense")

if submitted:
    date_str = date.strftime('%Y-%m-%d')
    
    # Reload dataframe
    df = pd.read_excel(EXCEL_FILE)
    
    # Check if the category exists; if not, create it
    if category not in df.columns:
        df[category] = None  # Add the category column with initial value None
    
    # If the date exists in the DataFrame, add the new expense to the existing one
    if date_str in df['Date'].astype(str).values:
        current_amount = df.loc[df['Date'].astype(str) == date_str, category].values
        if current_amount.size > 0 and pd.notna(current_amount[0]):
            # Add the new amount to the existing amount
            df.loc[df['Date'].astype(str) == date_str, category] += amount
        else:
            # If no amount exists (NaN), set the new amount
            df.loc[df['Date'].astype(str) == date_str, category] = amount
    else:
        # Add a new row if the date does not exist
        new_row = {col: None for col in df.columns}
        new_row['Date'] = date_str
        new_row[category] = amount
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Combine rows with the same date into one row
    df = df.groupby('Date', as_index=False).sum()

    # Reorder columns before saving (Date first)
    cols = ['Date'] + [col for col in df.columns if col != 'Date']
    df = df[cols]
    
    # Save updated DataFrame to Excel
    df.to_excel(EXCEL_FILE, index=False)
    
    st.success(f"Added {amount} to {category} on {date_str}")
    st.rerun()  # refresh view

# --- Show current table ---
st.subheader("Current Expenses")

# --- Compute totals for each category ---
if len(df) > 0:
    category_cols = [col for col in df.columns if col != 'Date']
    totals = {col: df[col].sum(skipna=True) for col in category_cols}
    total_row = {'Date': 'Total'}
    total_row.update(totals)
    df_display = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
else:
    df_display = df

# Ensure Date column is first and convert Date column to datetime
df_display['Date'] = pd.to_datetime(df_display['Date'], errors='coerce')  # Convert Date to datetime
df_display = df_display.sort_values(by='Date', ascending=True).reset_index(drop=True)

# Ensure Date column is first
cols = ['Date'] + [col for col in df_display.columns if col != 'Date']
df_display = df_display[cols]

st.dataframe(df_display.fillna(""))  # display without NaN

# --- Analytics Graph: Expense per Category (Pie Chart) ---
st.subheader("Expense Analytics (Pie Chart)")

if len(df) > 0:
    # Group by categories and sum the expenses, avoiding NaN values
    category_sums = {col: df[col].sum(skipna=True) for col in df.columns if col != 'Date'}
    
    # Create DataFrame for plotting
    category_df = pd.DataFrame(list(category_sums.items()), columns=['Category', 'Total Expense'])
    
    # Plotting the pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(category_df['Total Expense'], labels=category_df['Category'], autopct='%1.1f%%', startangle=90)
    plt.title("Expenses by Category")
    st.pyplot(plt)
