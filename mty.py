import pandas as pd
import streamlit as st
from io import BytesIO

# Load your Excel data
file_path = 'ContainerActivity.xlsx'
sheet_name = 'Sheet1'  # Adjust if needed

# Read the Excel file
data = pd.read_excel(file_path, sheet_name=sheet_name)

# Display the title of the app
st.title("Container Summary")

# Create tabs for different activity modes
tab_empty, tab_on_the_way = st.tabs(["Empty", "On The Way"])

# Function to create the pivot table and summary for a specific activity mode
def create_empty_pivot_table(activity_mode):
    # Dropdown for Region Name
    region_options = data['Region Name'].unique()
    selected_region = st.selectbox("Select Region Name:", region_options, key=f"region_{activity_mode}")

    # Dropdown for POL Port
    pol_options = data[data['Region Name'] == selected_region]['POL Port'].unique()
    selected_pol = st.selectbox("Select POL Port:", pol_options, key=f"pol_{activity_mode}")

    # Dropdown for Company
    company_options = data['Company'].unique().tolist()  # Get unique company names
    company_options.insert(0, "ALL")  # Add "ALL" option at the top
    selected_company = st.selectbox("Select Company:", company_options, key=f"company_{activity_mode}")

    # Filter data based on selections
    filtered_data = data[
        (data['Region Name'] == selected_region) &
        (data['POL Port'] == selected_pol) &
        (data['Activity Mode'] == activity_mode)
    ]

    # Additional filtering for Company selection
    if selected_company != "ALL":  # If not selecting all companies
        filtered_data = filtered_data[filtered_data['Company'] == selected_company]

    # Create the pivot table
    pivot_summary = pd.pivot_table(
        filtered_data,
        values='Container #',
        index='POL Agent',  # Use POL Agent as the index
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    # Add columns for total counts of 20' and 40' containers
    pivot_summary['Grand Total'] = pivot_summary.sum(axis=1)

    # Add total row
    pivot_summary.loc['Grand Total'] = pivot_summary.sum()

    # Display the pivot summary in the app
    st.write(f"Container Summary for {activity_mode}:")
    st.dataframe(pivot_summary)

    # Function to convert DataFrame to Excel for download
    def convert_df_to_excel(df, include_index=True):  # Include index by default
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=include_index)  # Set index based on parameter
        output.seek(0)
        return output

    # Download button for the summary (including POFD Agent names)
    excel_summary_file = convert_df_to_excel(pivot_summary, include_index=True)  # Ensure index is included
    st.download_button(
        label="Download Summary as Excel",
        data=excel_summary_file,
        file_name=f'{activity_mode.lower()}_summary.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Download button for the filtered data (without index)
    excel_filtered_file = convert_df_to_excel(filtered_data, include_index=False)  # Exclude index for filtered data
    st.download_button(
        label="Download Filtered Data as Excel",
        data=excel_filtered_file,
        file_name='filtered_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def create_on_the_way_pivot_table():
    # Dropdown for POFD Port
    pofd_port_options = data['POFD Port'].unique()
    selected_pofd_port = st.selectbox("Select POFD Port:", pofd_port_options, key="pofd_port")

    # Filter data based on POFD Port
    filtered_data = data[data['POFD Port'] == selected_pofd_port]

    # Create the pivot table for On The Way
    pivot_summary = pd.pivot_table(
        filtered_data,
        values='Container #',
        index='POFD Agent',  # Use POFD Agent as the index
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    # Add columns for total counts of 20' and 40' containers
    pivot_summary['Grand Total'] = pivot_summary.sum(axis=1)

    # Add total row
    pivot_summary.loc['Grand Total'] = pivot_summary.sum()

    # Display the pivot summary in the app
    st.write("Container Summary for On The Way:")
    st.dataframe(pivot_summary)

    # Function to convert DataFrame to Excel for download
    def convert_df_to_excel(df, include_index=True):  # Include index by default
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(write
