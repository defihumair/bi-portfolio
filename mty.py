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

# Tab structure for different summaries
tab1, tab2 = st.tabs(["MYT Containers", "On The Way"])

# =================== Tab 1: MYT Containers ===================
with tab1:
    # Dropdown for Region Name
    region_options = data['Region Name'].unique()
    selected_region = st.selectbox("Select Region Name:", region_options, key='myt_region')

    # Dropdown for POL Port
    pol_options = data[data['Region Name'] == selected_region]['POL Port'].unique()
    selected_pol = st.selectbox("Select POL Port:", pol_options, key='myt_pol')

    # Dropdown for Activity Mode
    activity_options = ['Empty', 'On The Way', 'Utilized']
    selected_activity = st.selectbox("Select Activity Mode:", activity_options, key='myt_activity')

    # Dropdown for Company
    company_options = data['Company'].unique().tolist()  # Get unique company names
    company_options.insert(0, "ALL")  # Add "ALL" option at the top
    selected_company = st.selectbox("Select Company:", company_options, key='myt_company')

    # Dropdown for Type
    type_options = ['Dry', 'Special']
    selected_type = st.selectbox("Select Type:", type_options, key='myt_type')

    # Define size categories based on the selected type
    if selected_type == 'Dry':
        size_categories = ['Heavy Duty', 'Hi-Cube']
    elif selected_type == 'Special':
        size_categories = ['Flat Rack', 'Open Top', 'Reefer', 'Standard']
    else:
        size_categories = []

    # Filter data based on selections
    filtered_data = data[
        (data['Region Name'] == selected_region) &
        (data['POL Port'] == selected_pol) &
        (data['Activity Mode'] == selected_activity) &
        (data['Type'].isin(size_categories))
    ]

    # Additional filtering for Company selection
    if selected_company != "ALL":  # If not selecting all companies
        filtered_data = filtered_data[filtered_data['Company'] == selected_company]

    # Include only 20' and 40' in the pivot table
    pivot_summary = pd.pivot_table(
        filtered_data,
        values='Container #',
        index='POL Agent',  # Keep this to show agent names
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    # Add columns for total counts of 20' and 40' containers
    pivot_summary['Grand Total'] = pivot_summary.sum(axis=1)

    # Add total row
    pivot_summary.loc['Grand Total'] = pivot_summary.sum()

    # Display the pivot summary in the app
    st.write("Container Summary:")
    st.dataframe(pivot_summary)

    # Function to convert DataFrame to Excel for download
    def convert_df_to_excel(df, include_index=True):  # Include index by default
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Data', index=include_index)  # Set index based on parameter
        output.seek(0)
        return output

    # Download button for the summary (including POL Agent names)
    excel_summary_file = convert_df_to_excel(pivot_summary, include_index=True)  # Ensure index is included
    st.download_button(
        label="Download Summary as Excel",
        data=excel_summary_file,
        file_name='container_summary.xlsx',
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

# =================== Tab 2: On The Way ===================
with tab2:
    # Dropdown for POFD Port
    pofd_port_options = data['POFD Port'].unique()
    selected_pofd_port = st.selectbox("Select POFD Port:", pofd_port_options, key='on_the_way_pofd')

    # Dropdown for Company
    company_options_on_the_way = data['Company'].unique().tolist()  # Get unique company names
    company_options_on_the_way.insert(0, "ALL")  # Add "ALL" option at the top
    selected_company_on_the_way = st.selectbox("Select Company:", company_options_on_the_way, key='on_the_way_company')

    # Filter data for "On The Way" summary
    on_the_way_data = data[data['Activity Mode'] == 'On The Way']

    # Further filter for the selected POFD Port
    filtered_on_the_way = on_the_way_data[on_the_way_data['POFD Port'] == selected_pofd_port]

    # Additional filtering for Company selection
    if selected_company_on_the_way != "ALL":  # If not selecting all companies
        filtered_on_the_way = filtered_on_the_way[filtered_on_the_way['Company'] == selected_company_on_the_way]

    # Create the pivot table for "On The Way" summary by POFD Agent
    pofd_pivot_summary = pd.pivot_table(
        filtered_on_the_way,
        values='Container #',
        index='POFD Agent',  # Index by POFD Agent
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    # Add columns for total counts of 20' and 40' containers
    pofd_pivot_summary['Grand Total'] = pofd_pivot_summary.sum(axis=1)

    # Add total row
    pofd_pivot_summary.loc['Grand Total'] = pofd_pivot_summary.sum()

    # Display the pivot summary for "On The Way" in the app
    st.write("On The Way Container Summary:")
    st.dataframe(pofd_pivot_summary)

    # Download button for the "On The Way" summary
    excel_on_the_way_file = convert_df_to_excel(pofd_pivot_summary, include_index=True)  # Include index
    st.download_button(
        label="Download On The Way Summary as Excel",
        data=excel_on_the_way_file,
        file_name='on_the_way_summary.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Download button for the filtered "On The Way" data
    excel_filtered_on_the_way_file = convert_df_to_excel(filtered_on_the_way, include_index=False)  # Exclude index for filtered data
    st.download_button(
        label="Download Filtered On The Way Data as Excel",
        data=excel_filtered_on_the_way_file,
        file_name='filtered_on_the_way_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
