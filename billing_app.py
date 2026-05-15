import streamlit as st
import pandas as pd
import openpyxl
from io import BytesIO

# --- PAGE SETUP ---
st.set_page_config(page_title="Reconciliation Portal", layout="wide")
st.title("📦 Logistics Billing Reconciliation Portal")
st.markdown("Upload your weekly files below to automatically reconcile and generate the payable invoice.")

# --- UPLOAD ZONE ---
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
    
    # 2. Reconcile (Merge & Calculate)
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
    
    st.divider()
    
    # --- HUMAN IN THE LOOP: APPROVAL ---
    st.subheader("⚙️ Finalize & Generate")
    
    if st.button("APPROVE & GENERATE PAYABLE INVOICE", type="primary"):
        with st.spinner("Injecting data into Excel Template..."):
            
            # Load the uploaded template into memory
            wb = openpyxl.load_workbook(template_file)
            sheet = wb.active
            
# --- DATA INJECTION LOGIC ---

# 1. Map the Billing Heads to their exact Row Numbers in your Excel Template
# (Note: If "No. of Containers" starts on Row 9 in your Excel file, keep this as is. 
# If it starts on Row 10, just change the 9 to 10 and adjust the rest down by 1).
ROW_MAP = {
    "No. of Containers": 9,
    "Total CBM": 10,
    "Remaining CBM {less(Levis, Removal & Pallets cargo)}": 11,
    "Total Levis OB CBM": 12,
    "Levis IB (Without Conveyor)": 13,
    "Levis IB Conveyor CBM(by Bahadur)": 14,
    "CY Cross Stuffing": 15,
    "Commercial, LCL, TPP, Cargo Removal": 16,
    "CARGO SHIFTING + SETTING CBM": 17,
    "Sorting Charges (Per Carton)": 18,
    "Sorting Charges LEVI'S (Per Carton)": 19,
    "Sunday Working": 20,
    "Hanging Cargo Charges": 21,
    "Labelling/Stickers Charges": 22,
    "CARTONS CHANGE": 23
}

# 2. Map the Facility to their exact Qty and Amount Columns in Excel
COL_MAP = {
    "Shed-1": {"qty": "C", "amt": "E"},
    "Shed-4": {"qty": "H", "amt": "J"},
    "Shed-6": {"qty": "M", "amt": "O"},
    "Commercial": {"qty": "R", "amt": "T"}
}

# 3. The Injection Loop (This does all the heavy lifting instantly)
# We loop through your final Vendor Data exactly as you exported it
for index, row in df_vendor.iterrows():
    billing_head = row['Billing Head']
    facility = row['Facility']
    qty = row['Sum of Qty']
    amount = row['Sum of Amount']
    
    # Check if this row's billing head and facility exist in our map
    if billing_head in ROW_MAP and facility in COL_MAP:
        
        # Get the GPS Coordinates
        target_row = ROW_MAP[billing_head]
        qty_col = COL_MAP[facility]['qty']
        amt_col = COL_MAP[facility]['amt']
        
        # INJECT THE DATA!
        # Example: sheet['C11'] = 146
        sheet[f"{qty_col}{target_row}"] = qty
        sheet[f"{amt_col}{target_row}"] = amount

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
                file_name="FINAL_Payable_Invoice_Bahadur.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
else:
    st.info("👆 Please upload all three files to begin the reconciliation process.")
