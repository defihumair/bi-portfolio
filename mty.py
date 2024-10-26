import pandas as pd
import streamlit as st

# Load your Excel data
file_path = 'ContainerActivity.xlsx'
sheet_name = 'Sheet1'  # Adjust if needed

# Read the Excel file
data = pd.read_excel(file_path, sheet_name=sheet_name)

# Display the title of the app
st.title("Container Summary")

# Dropdown for Region Name
region_options = data['Region Name'].unique()
selected_region = st.selectbox("Select Region Name:", region_options)

# Dropdown for POL Port
pol_options = data[data['Region Name'] == selected_region]['POL Port'].unique()
selected_pol = st.selectbox("Select POL Port:", pol_options)

# Dropdown for Activity Mode
activity_options = ['Empty']
selected_activity = st.selectbox("Select Activity Mode:", activity_options)

# Dropdown for Type
type_options = ['Dry', 'Special']
selected_type = st.selectbox("Select Type:", type_options)

# Define categories for the Type selection
if selected_type == 'Dry':
    size_options = ['Heavy Duty', 'Hi-Cube']
elif selected_type == 'Special':
    size_options = ['Flat Rack', 'Open Top', 'Reefer', 'Standard']
else:
    size_options = []

# Dropdown for Size
selected_size = st.selectbox("Select Size:", size_options)

# Filter data based on selections
filtered_data = data[
    (data['Region Name'] == selected_region) &
    (data['POL Port'] == selected_pol) &
    (data['Activity Mode'] == selected_activity) &
    (data['Type'] == selected_size)
]

# Pivot table to summarize counts of Container # by POL Agent and Size
pivot_summary = pd.pivot_table(
    filtered_data,
    values='Container #',
    index='POL Agent',
    columns='Size',
    aggfunc='count',
    fill_value=0
)

# Adding Grand Total columns and rows
pivot_summary.loc['Grand Total'] = pivot_summary.sum()
pivot_summary['Grand Total'] = pivot_summary.sum(axis=1)

# Display the pivot summary in the app
st.write("Container Summary:")
st.dataframe(pivot_summary)

# Save the summary to a new Excel file if needed (optional)
# summary_file_path = 'E:/DashApp ContainerActivity/Summary.xlsx'
# pivot_summary.to_excel(summary_file_path)
# st.success(f"Summary saved to {summary_file_path}")
