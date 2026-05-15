import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO
import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Reconciliation Portal", layout="wide")
st.title("📦 Logistics Billing Reconciliation Portal")
st.markdown("Upload your weekly files below to automatically reconcile and generate the payable invoice.")

# --- INVOICE DETAILS (NEW) ---
st.subheader("📝 1. Invoice Details")
col_date, col_week, col_year = st.columns(3)

with col_date:
    default_date = datetime.datetime.now().strftime("%d-%b-%Y")
    invoice_date = st.text_input("Invoice Date", value=default_date)

with col_week:
    week_num = st.number_input("Week Number (e.g., 19)", min_value=1, max_value=52, value=19)

with col_year:
    year_num = st.number_input("Year (e.g., 2026)", min_value=2020, max_value=2050, value=2026)

invoice_suffix = f"{week_num}{str(year_num)[-2:]}"

st.divider()

# --- UPLOAD ZONE ---
st.subheader("📂 2. Upload Files")
col1, col2, col3 = st.columns(3)
with col1:
    club_file = st.file_uploader("1. Upload Club Data (CSV)", type=['csv'])
with col2:
    vendor_file = st.file_uploader("2. Upload Vendor Invoice (CSV)", type=['csv'])
with col3:
    template_file = st.file_uploader("3. Upload Blank Excel Template", type=['xlsx'])

st.divider()

# --- PROCESSING ENGINE ---
if club_file and vendor_file and template_file:
    
    # 1. Read Data
    df_club = pd.read_csv(club_file)
    df_vendor = pd.read_csv(vendor_file)
    
    # 2. Reconcile (Merge & Calculate Dashboard)
    try:
        df_recon = pd.merge(df_club, df_vendor, on=['Billing Head', 'Facility'], how='outer').fillna(0)
        df_recon['Amount Variance'] = df_recon['Internal Amount'] - df_recon['Vendor Amount']
        
        # 3. Display Dashboard on Screen
        st.subheader("📊 Variance Summary")
        
        # Filter for discrepancies
        discrepancies = df_recon[df_recon['Amount Variance'] != 0]
        
        if discrepancies.empty:
            st.success("✅ PERFECT MATCH! No financial variances detected. Safe to generate.")
        else:
            st.error("⚠️ VARIANCES DETECTED! Please review before approving.")
            st.dataframe(discrepancies[['Billing Head', 'Facility', 'Internal Amount', 'Vendor Amount', 'Amount Variance']], use_container_width=True)
        
        st.metric("Total Net Variance (PKR)", f"{df_recon['Amount Variance'].sum():,.2f}")
        
    except KeyError:
        # If your Club Data CSV doesn't have 'Internal Amount' or 'Facility' yet, it skips the dashboard but still lets you print!
        st.warning("⚠️ Dashboard Preview skipped. (Ensure Club Data has 'Billing Head', 'Facility', and 'Internal Amount' columns to view the preview).")
    
    st.divider()
    
    # --- HUMAN IN THE LOOP: APPROVAL ---
    st.subheader("⚙️ 3. Finalize & Generate")
    
    if st.button("APPROVE & GENERATE PAYABLE INVOICE", type="primary"):
        with st.spinner("Injecting data into Excel Template..."):
            
            # Load the uploaded template into memory
            wb = openpyxl.load_workbook(template_file)
            sheet = wb.active
            
            # --- HEADER INJECTION LOGIC (FINAL VERIFIED COORDINATES) ---
            
            week_header_text = f"WEEK {week_num}, {year_num}"   # e.g., "WEEK 19, 2026"
            
            # --- SHED-1 ---
            sheet['F4'] = invoice_date                          # Date value next to E4
            sheet['F5'] = f"BCO/PW1/{invoice_suffix}"           # Invoice value next to E5
            sheet['B10'] = week_header_text                     # Week & Year Header
            
            # --- SHED-4 ---
            sheet['L4'] = invoice_date
            sheet['L5'] = f"BCO/PW4/{invoice_suffix}"
            sheet['H10'] = week_header_text
            
            # --- SHED-6 ---
            sheet['R4'] = invoice_date
            sheet['R5'] = f"BCO/PW6/{invoice_suffix}"
            sheet['N10'] = week_header_text
            
            # --- COMMERCIAL ---
            sheet['X4'] = invoice_date
            sheet['X5'] = f"BCO/PWC1/{invoice_suffix}"
            sheet['T10'] = week_header_text

            # --- DATA INJECTION LOGIC ---
            
            ROW_MAP = {
                "No. of Containers": 11,
                "Total CBM": 12,
                "Remaining CBM {less(Levis, Removal & Pallets cargo)}": 13,
                "Total Levis OB CBM": 14,
                "Levis IB (Without Conveyor)": 15,
                "Levis IB Conveyor CBM(by Bahadur)": 16,
                "CY Cross Stuffing": 17,
                "Commercial, LCL, TPP, Cargo Removal": 18,
                "CARGO SHIFTING + SETTING CBM": 19,
                "Sorting Charges (Per Carton)": 20,
                "Sorting Charges LEVI'S (Per Carton)": 21,
                "Sunday Working": 22,
                "Hanging Cargo Charges": 23,
                "Labelling/Stickers Charges": 24,
                "CARTONS CHANGE": 25
            }

            # UPDATED COLUMN MAP 
            COL_MAP = {
                "Shed-1": {"qty": "D", "amt": "F"},
                "Shed-4": {"qty": "J", "amt": "L"},
                "Shed-6": {"qty": "P", "amt": "R"},
                "Commercial": {"qty": "V", "amt": "X"}
            }

            # The Injection Loop 
            for index, row in df_vendor.iterrows():
                billing_head = row['Billing Head']
                facility = row['Facility']
                qty = row['Sum of Qty']
                amount = row['Sum of Amount']
                
                # Check if this row's billing head and facility exist in our map
                if billing_head in ROW_MAP and facility in COL_MAP:
                    target_row = ROW_MAP[billing_head]
                    qty_col = COL_MAP[facility]['qty']
                    amt_col = COL_MAP[facility]['amt']
                    
                    # INJECT THE DATA!
                    sheet[f"{qty_col}{target_row}"] = qty
                    sheet[f"{amt_col}{target_row}"] = amount

            # ---------------------------------------------------------
            # --- FORMULA INJECTION LOGIC (ROWS 26, 27, 28) ---
            # Python writes the actual Excel formulas into the final sheet
            
            # SHED-1 (Amount Column is F)
            sheet['F26'] = "=SUM(F11:F25)"
            sheet['F27'] = "=F26*0.15"
            sheet['F28'] = "=F26+F27"
            
            # SHED-4 (Amount Column is L)
            sheet['L26'] = "=SUM(L11:L25)"
            sheet['L27'] = "=L26*0.15"
            sheet['L28'] = "=L26+L27"
            
            # SHED-6 (Amount Column is R)
            sheet['R26'] = "=SUM(R11:R25)"
            sheet['R27'] = "=R26*0.15"
            sheet['R28'] = "=R26+R27"
            
            # COMMERCIAL (Amount Column is X)
            sheet['X26'] = "=SUM(X11:X25)"
            sheet['X27'] = "=X26*0.15"
            sheet['X28'] = "=X26+X27"
            # ---------------------------------------------------------
            
            # Save the modified workbook to a virtual file in memory
            virtual_workbook = BytesIO()
            wb.save(virtual_workbook)
            virtual_workbook.seek(0)
            
            st.success("🎉 Invoice Generated Successfully!")
            
            # Provide the Download Button
            st.download_button(
                label="⬇️ DOWNLOAD FINAL INVOICE",
                data=virtual_workbook,
                file_name=f"FINAL_Payable_Invoice_Bahadur_W{week_num}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("👆 Please upload all three files to begin the reconciliation process.")
