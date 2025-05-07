import streamlit as st
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load Google Sheets credentials from Streamlit secrets
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], 
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

# Create a service client for Google Sheets API
service = build('sheets', 'v4', credentials=creds)
SPREADSHEET_ID = '1ppuD28GiuYtzZO1MInM3XNNM_k4Jnusd5ahaG7zktP0'

# Get the sheet data
def get_sheet_data():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="Sheet1!A1:Z1000").execute()
    values = result.get('values', [])
    if not values:
        return pd.DataFrame()  # Return an empty DataFrame if no data exists
    df = pd.DataFrame(values[1:], columns=values[0])  # Skip the header row and assign columns
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Ensure 'Date' is in datetime format
    return df

# --- Load or initialize Google Sheets ---
df = get_sheet_data()

st.title("Expense Tracker 📊")

# --- Input Form ---
with st.form("expense_form"):
    date = st.date_input("Select Date")
    category = st.text_input("Enter Category")
    amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")
    submitted = st.form_submit_button("Save Expense")

if submitted:
    date_str = date.strftime('%Y-%m-%d')
    date_obj = pd.to_datetime(date_str)

    # Check if the date exists in the DataFrame, if not, add a new row
    if date_obj in df['Date'].values:
        if category not in df.columns:
            df[category] = None  # Add category column if it doesn't exist
        current_amount = df.loc[df['Date'] == date_obj, category].values
        if current_amount.size > 0 and pd.notna(current_amount[0]):
            df.loc[df['Date'] == date_obj, category] += amount  # Update existing value
        else:
            df.loc[df['Date'] == date_obj, category] = amount  # Add new value for category
    else:
        new_row = {col: None for col in df.columns}
        new_row['Date'] = date_obj
        new_row[category] = amount
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)  # Use concat instead of append

    # Write back the updated data to Google Sheets
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": df.values.tolist()}
    ).execute()

    st.success(f"Added {amount} to {category} on {date_str}")
    st.rerun()
