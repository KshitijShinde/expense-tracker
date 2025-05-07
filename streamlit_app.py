import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Setup Google Sheets API access
def get_google_sheet():
    # Load credentials from the Streamlit secrets
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"])

    # Authorize and create a client for the Sheets API
    gc = gspread.authorize(creds)

    # Open the Google Sheet by ID (paste the Sheet ID here)
    sheet = gc.open_by_key("1ppuD28GiuYtzZO1MInM3XNNM_k4Jnusd5ahaG7zktP0")
    worksheet = sheet.get_worksheet(0)
    return worksheet

# --- Load or initialize Google Sheets ---
worksheet = get_google_sheet()

# Read the sheet into a DataFrame
data = worksheet.get_all_records()
df = pd.DataFrame(data)

st.title("Expense Tracker 📊")

# --- Input Form ---
with st.form("expense_form"):
    date = st.date_input("Select Date")
    category = st.text_input("Enter Category")
    amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Save Expense")

if submitted:
    date_str = date.strftime('%Y-%m-%d')
    
    # Check if the date exists in the DataFrame, if not, add a new row
    if date_str in df['Date'].astype(str).values:
        if category not in df.columns:
            df[category] = None  # Add the column if it doesn't exist
        current_amount = df.loc[df['Date'].astype(str) == date_str, category].values
        if current_amount.size > 0 and pd.notna(current_amount[0]):
            df.loc[df['Date'].astype(str) == date_str, category] += amount
        else:
            df.loc[df['Date'].astype(str) == date_str, category] = amount
    else:
        new_row = {col: None for col in df.columns}
        new_row['Date'] = date_str
        new_row[category] = amount
        df = df.append(new_row, ignore_index=True)

    # Write back the updated data to Google Sheets
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    
    st.success(f"Added {amount} to {category} on {date_str}")
    st.rerun()

# --- Delete Expense Section ---
st.subheader("Delete Expense")

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
            
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
            st.rerun()

else:
    st.info("No data available for deletion.")
