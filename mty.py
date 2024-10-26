import pandas as pd
import streamlit as st
from io import BytesIO

def convert_df_to_excel(df: pd.DataFrame, include_index: bool = True) -> BytesIO:
    """
    Convert a DataFrame to an Excel file.

    Parameters:
    df (pd.DataFrame): DataFrame to convert.
    include_index (bool): Whether to include index in the Excel file.

    Returns:
    BytesIO: Excel file as a BytesIO object.
    """
    # Create a BytesIO object to save the Excel file
    output = BytesIO()
    
    # Use pandas Excel writer to save the DataFrame to the BytesIO object
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=include_index)
        
    # Seek to the beginning of the BytesIO object
    output.seek(0)
    return output

# Load your Excel data
file_path = 'ContainerActivity.xlsx'
sheet_name = 'Sheet1'  # Adjust if needed

# Read the Excel file
data = pd.read_excel(file_path, sheet_name=sheet_name)

# Display the title of the app
st.title("Container Summary")

# Tab structure for different summaries
tab1, tab2, tab3 = st.tabs(["MYT Containers", "On The Way", "Utilized"])

# =================== Tab 1: MYT Containers ===================
with tab1:
    # Dropdown for Region Name
    region_options_myt = data['Region Name'].unique()
    selected_region_myt = st.selectbox("Select Region Name:", region_options_myt, key='myt_region')

    # Dropdown for POL Port based on selected Region with "ALL" option
    pol_options_myt = data[data['Region Name'] == selected_region_myt]['POL Port'].unique().tolist()
    pol_options_myt.insert(0, "ALL")  # Add "ALL" option
    selected_pol_myt = st.selectbox("Select POL Port:", pol_options_myt, key='myt_pol')

    # Dropdown for Company
    company_options_myt = data['Company'].unique().tolist()
    company_options_myt.insert(0, "ALL")
    selected_company_myt = st.selectbox("Select Company:", company_options_myt, key='myt_company')

    # Filter data for MYT summary (only for Empty Activity Mode)
    myt_data = data[data['Activity Mode'] == 'Empty']

    # Further filter based on selected POL Port and Company
    filtered_myt = myt_data[
        (myt_data['Region Name'] == selected_region_myt) &
        (myt_data['POL Port'].isin(pol_options_myt if selected_pol_myt == "ALL" else [selected_pol_myt])) &
        (myt_data['Company'].isin(company_options_myt if selected_company_myt == "ALL" else [selected_company_myt]))
    ]

    # Create the pivot table for MYT summary by POL Agent
    myt_pivot_summary = pd.pivot_table(
        filtered_myt,
        values='Container #',
        index='POL Agent',
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    # Add columns for total counts of 20' and 40' containers
    myt_pivot_summary['Grand Total'] = myt_pivot_summary.sum(axis=1)

    # Add total row
    myt_pivot_summary.loc['Grand Total'] = myt_pivot_summary.sum()

    # Display the pivot summary for MYT in the app
    st.write("MYT Container Summary:")
    st.dataframe(myt_pivot_summary)

    # Download button for the MYT summary
    excel_myt_file = convert_df_to_excel(myt_pivot_summary, include_index=True)
    st.download_button(
        label="Download MYT Summary as Excel",
        data=excel_myt_file,
        file_name='myt_summary.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Download button for the filtered MYT data
    excel_filtered_myt_file = convert_df_to_excel(filtered_myt, include_index=False)
    st.download_button(
        label="Download Filtered MYT Data as Excel",
        data=excel_filtered_myt_file,
        file_name='filtered_myt_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# =================== Tab 2: On The Way ===================
with tab2:
    # Dropdown for POFD Port
    pofd_port_options = data['POFD Port'].unique()
    selected_pofd_port = st.selectbox("Select POFD Port:", pofd_port_options, key='on_the_way_pofd')

    # Dropdown for Company
    company_options_on_the_way = data['Company'].unique().tolist()
    company_options_on_the_way.insert(0, "ALL")
    selected_company_on_the_way = st.selectbox("Select Company:", company_options_on_the_way, key='on_the_way_company')

    # Filter data for "On The Way" summary
    on_the_way_data = data[data['Activity Mode'] == 'On The Way']

    # Further filter for the selected POFD Port
    filtered_on_the_way = on_the_way_data[on_the_way_data['POFD Port'] == selected_pofd_port]

    # Additional filtering for Company selection
    if selected_company_on_the_way != "ALL":
        filtered_on_the_way = filtered_on_the_way[filtered_on_the_way['Company'] == selected_company_on_the_way]

    # Create the pivot table for "On The Way" summary by POFD Agent
    pofd_pivot_summary = pd.pivot_table(
        filtered_on_the_way,
        values='Container #',
        index='POFD Agent',
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
    excel_on_the_way_file = convert_df_to_excel(pofd_pivot_summary, include_index=True)
    st.download_button(
        label="Download On The Way Summary as Excel",
        data=excel_on_the_way_file,
        file_name='on_the_way_summary.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Download button for the filtered "On The Way" data
    excel_filtered_on_the_way_file = convert_df_to_excel(filtered_on_the_way, include_index=False)
    st.download_button(
        label="Download Filtered On The Way Data as Excel",
        data=excel_filtered_on_the_way_file,
        file_name='filtered_on_the_way_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# =================== Tab 3: Utilized ===================
with tab3:
    # Dropdown for Region Name
    region_options_utilized = data['Region Name'].unique()
    selected_region_utilized = st.selectbox("Select Region Name:", region_options_utilized, key='utilized_region')

    # Dropdown for POL Port based on selected Region with "ALL" option
    pol_options_utilized = data[data['Region Name'] == selected_region_utilized]['POL Port'].unique().tolist()
    pol_options_utilized.insert(0, "ALL")  # Add "ALL" option
    selected_pol_utilized = st.selectbox("Select POL Port:", pol_options_utilized, key='utilized_pol')

    # Dropdown for Company
    company_options_utilized = data['Company'].unique().tolist()
    company_options_utilized.insert(0, "ALL")
    selected_company_utilized = st.selectbox("Select Company:", company_options_utilized, key='utilized_company')

    # Filter data for Utilized summary (for specific Activities)
    utilized_data = data[data['Activity'].isin(['DISCHARGE FULL', 'SENT TO CONSIGNEE'])]

    # Further filter based on selected POL Port and Company
    filtered_utilized = utilized_data[
        (utilized_data['Region Name'] == selected_region_utilized) &
        (utilized_data['POL Port'].isin(pol_options_utilized if selected_pol_utilized == "ALL" else [selected_pol_utilized])) &
        (utilized_data['Company'].isin(company_options_utilized if selected_company_utilized == "ALL" else [selected_company_utilized]))
    ]

    # Create the pivot table for Utilized summary by POL Agent
    utilized_pivot_summary = pd.pivot_table(
        filtered_utilized,
        values='Container #',
        index='POL Agent',
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    # Add columns for total counts of 20' and 40' containers
    utilized_pivot_summary['Grand Total'] = utilized_pivot_summary.sum(axis=1)

    # Add total row
    utilized_pivot_summary.loc['Grand Total'] = utilized_pivot_summary.sum()

    # Display the pivot summary for Utilized in the app
    st.write("Utilized Container Summary:")
    st.dataframe(utilized_pivot_summary)

    # Download button for the Utilized summary
    excel_utilized_file = convert_df_to_excel(utilized_pivot_summary, include_index=True)
    st.download_button(
        label="Download Utilized Summary as Excel",
        data=excel_utilized_file,
        file_name='utilized_summary.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    # Download button for the filtered Utilized data
    excel_filtered_utilized_file = convert_df_to_excel(filtered_utilized, include_index=False)
    st.download_button(
        label="Download Filtered Utilized Data as Excel",
        data=excel_filtered_utilized_file,
        file_name='filtered_utilized_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
