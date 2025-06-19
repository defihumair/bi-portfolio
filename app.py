import pandas as pd
import streamlit as st

# Load data from Excel
@st.cache_data
def load_data():
    file_path = r'E:\DashApp\ContainerActivity.xlsx'
    df = pd.read_excel(file_path)
    return df

def main():
    st.set_page_config(page_title='Container Search Tool', layout='centered')
    st.title('🔍 Container Search Tool')
    st.markdown('Enter one or more container numbers (comma, space, or newline separated) to find their related companies.')

    # Load data
    df = load_data()

    # Input for multiple container numbers
    container_input = st.text_area('Enter Container Numbers:', height=150, placeholder='e.g.\nTRLU6731648\nCCLU7227024')

    if container_input:
        # Normalize input into a list of container numbers
        containers = [c.strip().upper() for c in container_input.replace(',', '\n').split('\n') if c.strip()]

        # Filter the dataframe
        filtered = df[df['Container #'].str.upper().isin(containers)]

        if not filtered.empty:
            st.success(f'{len(filtered)} container(s) found.')
            st.dataframe(filtered[['Company', 'Container #']])
        else:
            st.error('No matching containers found.')

if __name__ == '__main__':
    main()
