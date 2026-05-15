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
    
    # 1. Read Raw Data
    df_club_raw = pd.read_csv(club_file)
    df_vendor_raw = pd.read_csv(vendor_file)
    
    # --- DATA TRANSFORMATION ENGINE ---
    try:
        df_vendor = df_vendor_raw.rename(columns={'Sum of Qty': 'Vendor Qty', 'Sum of Amount': 'Vendor Amount'})
        
        exclude_cols = ['Location', 'Account', 'Total Payment (WITHOUT TAX)']
        value_vars = [col for col in df_club_raw.columns if col not in exclude_cols]
        
        df_club_long = pd.melt(df_club_raw, id_vars=['Location', 'Account'], value_vars=value_vars, 
                               var_name='Billing Head', value_name='Internal Qty')
        
        df_club_long['Internal Qty'] = pd.to_numeric(df_club_long['Internal Qty'], errors='coerce').fillna(0)
        
        df_club_long['Facility'] = df_club_long.apply(
            lambda x: 'Commercial' if str(x['Account']).strip() == 'Commercial' else str(x['Location']).strip(), axis=1
        )
        
        df_club = df_club_long.groupby(['Billing Head', 'Facility'], as_index=False)['Internal Qty'].sum()
        
        # UPDATED RATE MAP (Levi's is 1.1)
        RATE_MAP = {
            "Remaining CBM {less(Levis, Removal & Pallets cargo)}": 92,
            "Total Levis OB CBM": 46,
            "Levis IB (Without Conveyor)": 46,
            "Levis IB Conveyor CBM(by Bahadur)": 71,
            "CY Cross Stuffing": 46,
            "Commercial, LCL, TPP, Cargo Removal": 92,
            "CARGO SHIFTING + SETTING CBM": 46,
            "Sorting Charges (Per Carton)": 2,
            "Sorting Charges LEVI'S (Per Carton)": 1.1,
            "Sunday Working": 46,
            "Hanging Cargo Charges": 1,
            "Labelling/Stickers Charges": 2,
            "CARTONS CHANGE": 10
        }
        
        df_club['Internal Rate'] = df_club['Billing Head'].map(RATE_MAP).fillna(0)
        df_club['Internal Amount'] = df_club['Internal Qty'] * df_club['Internal Rate']

        df_recon = pd.merge(df_club, df_vendor, on=['Billing Head', 'Facility'], how='outer').fillna(0)
        
        df_recon['Volume Variance'] = df_recon['Internal Qty'] - df_recon['Vendor Qty']
        df_recon['Amount Variance'] = df_recon['Internal Amount'] - df_recon['Vendor Amount']
        
        # --- BUSINESS RULES ENGINE (Facility by Facility) ---
        def apply_audit_rules(row):
            int_amt = round(float(row['Internal Amount']), 2)
            ven_amt = round(float(row['Vendor Amount']), 2)
            int_qty = float(row['Internal Qty'])
            ven_qty = float(row['Vendor Qty'])

            if int_amt == 0 and ven_amt == 0:
                if ven_qty > int_qty:
                    return pd.Series([int_qty, int_amt, "Vendor Overbilled (Vol) – Adjusted to tracker"])
                elif ven_qty < int_qty:
                    return pd.Series([ven_qty, ven_amt, "Vendor Underbilled (Vol) – Adjusted to vendor"])
                else:
                    return pd.Series([ven_qty, ven_amt, "Proceed with Vendor Billed"])

            if ven_amt > int_amt:
                return pd.Series([int_qty, int_amt, "Vendor Overbilled – Adjusted as per tracker volume"])
            elif ven_amt < int_amt:
                return pd.Series([ven_qty, ven_amt, "Vendor Underbilled – Adjusted as per vendor volumes"])
            else:
                return pd.Series([ven_qty, ven_amt, "Proceed with Vendor Billed"])

        df_recon[['Approved Qty', 'Payable Amount', 'Remarks']] = df_recon.apply(apply_audit_rules, axis=1)
        
        # --- 3. DASHBOARD TABULAR RECONSTRUCTION ---
        st.subheader("📊 Recon & Audit Dashboard")
        
        facilities = ['Shed-1', 'Shed-4', 'Shed-6', 'Commercial']
        billing_heads = df_recon['Billing Head'].unique()
        display_rows = []

        for bh in billing_heads:
            bh_data = df_recon[df_recon['Billing Head'] == bh]
            
            row_data = {('Activity', 'Billing Head'): bh}
            row_data[('Club Data', 'Rate')] = RATE_MAP.get(bh, 0)
            
            club_vol = 0
            for f in facilities:
                val = bh_data[bh_data['Facility'] == f]['Internal Qty'].sum()
                row_data[('Club Data', f)] = val
                club_vol += val
            row_data[('Club Data', 'Total Volume')] = club_vol
            
            total_int_amt = round(bh_data['Internal Amount'].sum(), 2)
            row_data[('Club Data', 'Internal Amount')] = total_int_amt
            
            vendor_vol = 0
            for f in facilities:
                val = bh_data[bh_data['Facility'] == f]['Vendor Qty'].sum()
                row_data[('Vendor Invoice Data', f)] = val
                vendor_vol += val
            row_data[('Vendor Invoice Data', 'Vendor Volume')] = vendor_vol
            
            total_ven_amt = round(bh_data['Vendor Amount'].sum(), 2)
            row_data[('Vendor Invoice Data', 'Vendor Amount')] = total_ven_amt
            
            row_data[('Variance Analysis', 'Volume Variance')] = bh_data['Volume Variance'].sum()
            row_data[('Variance Analysis', 'Amount Variance')] = bh_data['Amount Variance'].sum()
            row_data[('Variance Analysis', 'Approved Volume')] = bh_data['Approved Qty'].sum()
            row_data[('Variance Analysis', 'Payable Amount')] = bh_data['Payable Amount'].sum()
            
            # FIXED REMARKS LOGIC (Now calculates accurately for the Dashboard row totals)
            if total_int_amt == 0 and total_ven_amt == 0:
                if vendor_vol > club_vol:
                    summary_remark = "Vendor Overbilled (Vol) – Adjusted to tracker"
                elif vendor_vol < club_vol:
                    summary_remark = "Vendor Underbilled (Vol) – Adjusted to vendor"
                else:
                    summary_remark = "Proceed with Vendor Billed"
            else:
                if total_ven_amt > total_int_amt:
                    summary_remark = "Vendor Overbilled – Adjusted as per tracker volume"
                elif total_ven_amt < total_int_amt:
                    summary_remark = "Vendor Underbilled – Adjusted as per vendor volumes"
                else:
                    summary_remark = "Proceed with Vendor Billed"
                    
            row_data[('Variance Analysis', 'Remarks')] = summary_remark
            display_rows.append(row_data)

        df_display = pd.DataFrame(display_rows)
        df_display.columns = pd.MultiIndex.from_tuples(df_display.columns)
        
        st.dataframe(df_display, use_container_width=True)
        
        met1, met2, met3 = st.columns(3)
        met1.metric("Total Internal Amount", f"PKR {df_recon['Internal Amount'].sum():,.2f}")
        met2.metric("Total Vendor Invoice", f"PKR {df_recon['Vendor Amount'].sum():,.2f}")
        met3.metric("Final Approved Payable", f"PKR {df_recon['Payable Amount'].sum():,.2f}", 
                    delta=f"{df_recon['Payable Amount'].sum() - df_recon['Vendor Amount'].sum():,.2f} vs Vendor", 
                    delta_color="inverse")
        
    except KeyError as e:
        st.error(f"Transformation Error: Please ensure your files are correct. Missing column: {e}")
    
    st.divider()
    
    # --- HUMAN IN THE LOOP: APPROVAL ---
    st.subheader("⚙️ 3. Finalize & Generate")
    
    if st.button("APPROVE & GENERATE PAYABLE INVOICE", type="primary"):
        with st.spinner("Injecting audited data into Excel Template..."):
            
            wb = openpyxl.load_workbook(template_file)
            sheet = wb.active
            
            week_header_text = f"WEEK {week_num}, {year_num}" 
            
            sheet['F4'] = invoice_date; sheet['F5'] = f"BCO/PW1/{invoice_suffix}"; sheet['B10'] = week_header_text
            sheet['L4'] = invoice_date; sheet['L5'] = f"BCO/PW4/{invoice_suffix}"; sheet['H10'] = week_header_text
            sheet['R4'] = invoice_date; sheet['R5'] = f"BCO/PW6/{invoice_suffix}"; sheet['N10'] = week_header_text
            sheet['X4'] = invoice_date; sheet['X5'] = f"BCO/PWC1/{invoice_suffix}"; sheet['T10'] = week_header_text

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

            for index, row in df_recon.iterrows():
                billing_head = row['Billing Head']
                facility = row['Facility']
                qty = row['Approved Qty']        
                amount = row['Payable Amount']   
                
                if billing_head in ROW_MAP and facility in COL_MAP:
                    target_row = ROW_MAP[billing_head]
                    qty_col = COL_MAP[facility]['qty']
                    amt_col = COL_MAP[facility]['amt']
                    
                    sheet[f"{qty_col}{target_row}"] = qty
                    sheet[f"{amt_col}{target_row}"] = amount

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
