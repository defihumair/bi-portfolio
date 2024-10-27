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
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=include_index)
        
    output.seek(0)
    return output

# Load your Excel data
file_path = 'ContainerActivity.xlsx'
sheet_name = 'Sheet1'

data = pd.read_excel(file_path, sheet_name=sheet_name)

st.title("Container Summary By Humair")

# Define the dropdown options for Type
type_options = {
    "Dry": ["Heavy Duty", "Hi-Cube"],
    "Special": ["Flat Rack", "Open Top", "Reefer", "Standard"]
}

# Tab structure for different summaries
tab1, tab2, tab3 = st.tabs(["MYT Containers", "On The Way", "Utilized"])

# =================== Tab 1: MYT Containers ===================
with tab1:
    # Dropdown for Type
    selected_type_myt = st.selectbox("Select Type:", list(type_options.keys()), key='myt_type')
    
    # Get the subcategories based on selected type
    subcategories_myt = type_options[selected_type_myt]
    selected_subcategory_myt = st.selectbox("Select Subcategory:", subcategories_myt, key='myt_subcategory')

    # Dropdown for Region Name
    region_options_myt = data['Region Name'].unique()
    selected_region_myt = st.selectbox("Select Region Name:", region_options_myt, key='myt_region')

    pol_options_myt = data[data['Region Name'] == selected_region_myt]['POL Port'].unique().tolist()
    pol_options_myt.insert(0, "ALL")
    selected_pol_myt = st.selectbox("Select POL Port:", pol_options_myt, key='myt_pol')

    company_options_myt = data['Company'].unique().tolist()
    company_options_myt.insert(0, "ALL")
    selected_company_myt = st.selectbox("Select Company:", company_options_myt, key='myt_company')

    myt_data = data[data['Activity Mode'] == 'Empty']

    filtered_myt = myt_data[
        (myt_data['Region Name'] == selected_region_myt) &
        (myt_data['POL Port'].isin(pol_options_myt if selected_pol_myt == "ALL" else [selected_pol_myt])) &
        (myt_data['Company'].isin(company_options_myt if selected_company_myt == "ALL" else [selected_company_myt])) &
        (myt_data['Type'] == selected_subcategory_myt)  # Filter by subcategory
    ]

    myt_pivot_summary = pd.pivot_table(
        filtered_myt,
        values='Container #',
        index='POL Agent',
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    myt_pivot_summary['Grand Total'] = myt_pivot_summary.sum(axis=1)
    myt_pivot_summary.loc['Grand Total'] = myt_pivot_summary.sum()

    st.write("MYT Container Summary:")
    st.dataframe(myt_pivot_summary)

    excel_myt_file = convert_df_to_excel(myt_pivot_summary, include_index=True)
    st.download_button(
        label="Download MYT Summary as Excel",
        data=excel_myt_file,
        file_name='myt_summary.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    excel_filtered_myt_file = convert_df_to_excel(filtered_myt, include_index=False)
    st.download_button(
        label="Download Filtered MYT Data as Excel",
        data=excel_filtered_myt_file,
        file_name='filtered_myt_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# =================== Tab 2: On The Way ===================
with tab2:
    # Dropdown for Type
    selected_type_on_the_way = st.selectbox("Select Type:", list(type_options.keys()), key='on_the_way_type')
    
    subcategories_on_the_way = type_options[selected_type_on_the_way]
    selected_subcategory_on_the_way = st.selectbox("Select Subcategory:", subcategories_on_the_way, key='on_the_way_subcategory')

    pofd_port_options = data['POFD Port'].unique()
    selected_pofd_port = st.selectbox("Select POFD Port:", pofd_port_options, key='on_the_way_pofd')

    company_options_on_the_way = data['Company'].unique().tolist()
    company_options_on_the_way.insert(0, "ALL")
    selected_company_on_the_way = st.selectbox("Select Company:", company_options_on_the_way, key='on_the_way_company')

    on_the_way_data = data[data['Activity Mode'] == 'On The Way']

    filtered_on_the_way = on_the_way_data[on_the_way_data['POFD Port'] == selected_pofd_port]

    if selected_company_on_the_way != "ALL":
        filtered_on_the_way = filtered_on_the_way[filtered_on_the_way['Company'] == selected_company_on_the_way]

    filtered_on_the_way = filtered_on_the_way[filtered_on_the_way['Type'] == selected_subcategory_on_the_way]  # Filter by subcategory

    pofd_pivot_summary = pd.pivot_table(
        filtered_on_the_way,
        values='Container #',
        index='POFD Agent',
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    pofd_pivot_summary['Grand Total'] = pofd_pivot_summary.sum(axis=1)
    pofd_pivot_summary.loc['Grand Total'] = pofd_pivot_summary.sum()

    st.write("On The Way Container Summary:")
    st.dataframe(pofd_pivot_summary)

    excel_on_the_way_file = convert_df_to_excel(pofd_pivot_summary, include_index=True)
    st.download_button(
        label="Download On The Way Summary as Excel",
        data=excel_on_the_way_file,
        file_name='on_the_way_summary.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    excel_filtered_on_the_way_file = convert_df_to_excel(filtered_on_the_way, include_index=False)
    st.download_button(
        label="Download Filtered On The Way Data as Excel",
        data=excel_filtered_on_the_way_file,
        file_name='filtered_on_the_way_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# =================== Tab 3: Utilized ===================
with tab3:
    # Dropdown for Type
    selected_type_utilized = st.selectbox("Select Type:", list(type_options.keys()), key='utilized_type')
    
    subcategories_utilized = type_options[selected_type_utilized]
    selected_subcategory_utilized = st.selectbox("Select Subcategory:", subcategories_utilized, key='utilized_subcategory')

    region_options_utilized = data['Region Name'].unique()
    selected_region_utilized = st.selectbox("Select Region Name:", region_options_utilized, key='utilized_region')

    pol_options_utilized = data[data['Region Name'] == selected_region_utilized]['POL Port'].unique().tolist()
    pol_options_utilized.insert(0, "ALL")
    selected_pol_utilized = st.selectbox("Select POL Port:", pol_options_utilized, key='utilized_pol')

    company_options_utilized = data['Company'].unique().tolist()
    company_options_utilized.insert(0, "ALL")
    selected_company_utilized = st.selectbox("Select Company:", company_options_utilized, key='utilized_company')

    utilized_data = data[data['Activity'].isin(['DISCHARGE FULL', 'SENT TO CONSIGNEE'])]

    filtered_utilized = utilized_data[
        (utilized_data['Region Name'] == selected_region_utilized) &
        (utilized_data['POL Port'].isin(pol_options_utilized if selected_pol_utilized == "ALL" else [selected_pol_utilized])) &
        (utilized_data['Company'].isin(company_options_utilized if selected_company_utilized == "ALL" else [selected_company_utilized])) &
        (utilized_data['Type'] == selected_subcategory_utilized)  # Filter by subcategory
    ]

    utilized_pivot_summary = pd.pivot_table(
        filtered_utilized,
        values='Container #',
        index='POL Agent',
        columns='Size',
        aggfunc='count',
        fill_value=0
    )

    utilized_pivot_summary['Grand Total'] = utilized_pivot_summary.sum(axis=1)
    utilized_pivot_summary.loc['Grand Total'] = utilized_pivot_summary.sum()

    st.write("Utilized Container Summary:")
    st.dataframe(utilized_pivot_summary)

    # Fixing the missing parenthesis here
    excel_utilized_file = convert_df_to_excel(utilized_pivot_summary, include_index=True)
    st.download_button(
        label="Download Utilized Summary as Excel",
        data=excel_utilized_file,
        file_name='utilized_summary.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    excel_filtered_utilized_file = convert_df_to_excel(filtered_utilized, include_index=False)
    st.download_button(
        label="Download Filtered Utilized Data as Excel",
        data=excel_filtered_utilized_file,
        file_name='filtered_utilized_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
