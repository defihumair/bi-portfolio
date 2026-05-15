import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO
import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Reconciliation Portal", layout="wide")
st.title("📦 Logistics Billing Reconciliation Portal")
st.markdown("Upload your weekly files below to automatically reconcile, audit, and generate the payable invoice.")

# --- INVOICE DETAILS ---
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
    
    # Standardize Column Names (Handles slight variations in Power BI exports)
    df_vendor = df_vendor.rename(columns={'Sum of Qty': 'Vendor Qty', 'Sum of Amount': 'Vendor Amount'})
    df_club = df_club.rename(columns={'Internal Total Volume': 'Internal Qty'}) # Adjust if your Club Data uses a different Qty header
    
    # Ensure missing columns don't crash the script if headers vary
    if 'Internal Qty' not in df_club.columns: df_club['Internal Qty'] = df_club.get('Qty', 0)
    
    try:
        # 2. Reconcile (Merge)
        df_recon = pd.merge(df_club, df_vendor, on=['Billing Head', 'Facility'], how='outer').fillna(0)
        
        # Calculate Raw Variances
        df_recon['Volume Variance'] = df_recon['Internal Qty'] - df_recon['Vendor Qty']
        df_recon['Amount Variance'] = df_recon['Internal Amount'] - df_recon['Vendor Amount']
        
        # --- BUSINESS RULES ENGINE ---
        def apply_audit_rules(row):
            int_amt = float(row['Internal Amount'])
            ven_amt = float(row['Vendor Amount'])
            int_qty = float(row['Internal Qty'])
            ven_qty = float(row['Vendor Qty'])

            # Handle charges that don't have monetary amounts (like CBM tracking)
            if int_amt == 0 and ven_amt == 0:
                if ven_qty > int_qty:
                    return pd.Series([int_qty, int_amt, "Vendor Overbilled (Vol) – Adjusted to tracker"])
                elif ven_qty < int_qty:
                    return pd.Series([ven_qty, ven_amt, "Vendor Underbilled (Vol) – Adjusted to vendor"])
                else:
                    return pd.Series([ven_qty, ven_amt, "Proceed with Vendor Billed"])

            # Core Financial Audit Logic
            if ven_amt > int_amt:
                return pd.Series([int_qty, int_amt, "Vendor Overbilled – Adjusted as per tracker volume"])
            elif ven_amt < int_amt:
                return pd.Series([ven_qty, ven_amt, "Vendor Underbilled – Adjusted as per vendor volumes"])
            else:
                return pd.Series([ven_qty, ven_amt, "Proceed with Vendor Billed"])

        # Apply the rules to create the final Payable columns
        df_recon[['Approved Qty', 'Payable Amount', 'Remarks']] = df_recon.apply(apply_audit_rules, axis=1)
        
        # 3. Display Detailed Reconciliation Dashboard
        st.subheader("📊 Recon & Audit Dashboard")
        
        # Arrange columns to match your Excel layout perfectly
        display_cols = [
            'Billing Head', 'Facility', 
            'Internal Qty', 'Internal Amount', 
            'Vendor Qty', 'Vendor Amount', 
            'Volume Variance', 'Amount Variance', 
            'Approved Qty', 'Payable Amount', 'Remarks'
        ]
        
        st.dataframe(df_recon[display_cols], use_container_width=True)
        
        # Financial Summary metrics
        met1, met2, met3 = st.columns(3)
        met1.metric("Total Internal Amount", f"PKR {df_recon['Internal Amount'].sum():,.2f}")
        met2.metric("Total Vendor Invoice", f"PKR {df_recon['Vendor Amount'].sum():,.2f}")
        met3.metric("Final Approved Payable", f"PKR {df_recon['Payable Amount'].sum():,.2f}", 
                    delta=f"{df_recon['Payable Amount'].sum() - df_recon['Vendor Amount'].sum():,.2f} vs Vendor", 
                    delta_color="inverse")
        
    except KeyError as e:
        st.error(f"Column mismatch error: Please ensure your CSVs have 'Billing Head', 'Facility', 'Internal Amount', and 'Vendor Amount'. Missing: {e}")
    
    st.divider()
    
    # --- HUMAN IN THE LOOP: APPROVAL ---
    st.subheader("⚙️ 3. Finalize & Generate")
    
    if st.button("APPROVE & GENERATE PAYABLE INVOICE", type="primary"):
        with st.spinner("Injecting audited data into Excel Template..."):
            
            wb = openpyxl.load_workbook(template_file)
            sheet = wb.active
            
            # --- HEADER INJECTION LOGIC ---
            week_header_text = f"WEEK {week_num}, {year_num}" 
            
            sheet['F4'] = invoice_date; sheet['F5'] = f"BCO/PW1/{invoice_suffix}"; sheet['B10'] = week_header_text
            sheet['L4'] = invoice_date; sheet['L5'] = f"BCO/PW4/{invoice_suffix}"; sheet['H10'] = week_header_text
            sheet['R4'] = invoice_date; sheet['R5'] = f"BCO/PW6/{invoice_suffix}"; sheet['N10'] = week_header_text
            sheet['X4'] = invoice_date; sheet['X5'] = f"BCO/PWC1/{invoice_suffix}"; sheet['T10'] = week_header_text

            # --- DATA INJECTION LOGIC ---
            ROW_MAP = {
                "No. of Containers": 11, "Total CBM": 12, "Remaining CBM {less(Levis, Removal & Pallets cargo)}": 13,
                "Total Levis OB CBM": 14, "Levis IB (Without Conveyor)": 15, "Levis IB Conveyor CBM(by Bahadur)": 16,
                "CY Cross Stuffing": 17, "Commercial, LCL, TPP, Cargo Removal": 18, "CARGO SHIFTING + SETTING CBM": 19,
                "Sorting Charges (Per Carton)": 20, "Sorting Charges LEVI'S (Per Carton)": 21, "Sunday Working": 22,
                "Hanging Cargo Charges": 23, "Labelling/Stickers Charges": 24, "CARTONS CHANGE": 25
            }

            COL_MAP = {
                "Shed-1": {"qty": "D", "amt": "F"}, "Shed-4": {"qty": "J", "amt": "L"},
                "Shed-6": {"qty": "P", "amt": "R"}, "Commercial": {"qty": "V", "amt": "X"}
            }

            # The Injection Loop (NOW USING APPROVED QTY AND PAYABLE AMOUNT)
            for index, row in df_recon.iterrows():
                billing_head = row['Billing Head']
                facility = row['Facility']
                qty = row['Approved Qty']        # Pulled from Rules Engine
                amount = row['Payable Amount']   # Pulled from Rules Engine
                
                if billing_head in ROW_MAP and facility in COL_MAP:
                    target_row = ROW_MAP[billing_head]
                    qty_col = COL_MAP[facility]['qty']
                    amt_col = COL_MAP[facility]['amt']
                    
                    sheet[f"{qty_col}{target_row}"] = qty
                    sheet[f"{amt_col}{target_row}"] = amount

            # --- FORMULA INJECTION LOGIC ---
            sheet['F26'] = "=SUM(F11:F25)"; sheet['F27'] = "=F26*0.15"; sheet['F28'] = "=F26+F27"
            sheet['L26'] = "=SUM(L11:L25)"; sheet['L27'] = "=L26*0.15"; sheet['L28'] = "=L26+L27"
            sheet['R26'] = "=SUM(R11:R25)"; sheet['R27'] = "=R26*0.15"; sheet['R28'] = "=R26+R27"
            sheet['X26'] = "=SUM(X11:X25)"; sheet['X27'] = "=X26*0.15"; sheet['X28'] = "=X26+X27"
            
            virtual_workbook = BytesIO()
            wb.save(virtual_workbook)
            virtual_workbook.seek(0)
            
            st.success("🎉 Invoice Generated Successfully with Audited Adjustments!")
            
            st.download_button(
                label="⬇️ DOWNLOAD FINAL AUDITED INVOICE",
                data=virtual_workbook,
                file_name=f"FINAL_Payable_Invoice_Bahadur_W{week_num}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("👆 Please upload all three files to begin the reconciliation process.")
