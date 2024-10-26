import streamlit as st
import pandas as pd
import gdown

@st.cache_data
def load_data():
    # Google Drive file URL
    url = 'https://drive.google.com/uc?id=1HXuCnyEBdUfxfOrxocMXJ5DHYG2z3dO2'
    output = 'ContainerActivity.xlsx'  # Adjust the path as necessary
    # Download the file
    gdown.download(url, output, quiet=False)
    # Load the downloaded Excel file
    return pd.read_excel(file_path, usecols=['Container #', 'POL Port', 'POL Agent', 'Size', 'Ageing Days', 'Activity Mode', 'Type'])

# Load the Excel data
df = load_data()

# Define the container type categories
container_types = {
    'SPECIAL': ['Flat Rack', 'Open Top', 'Reefer', 'Standard'],
    'DRY': ['Heavy Duty', 'Hi-Cube']
}

# User input section
st.title("Container Agent Assignment")
input_port = st.text_input('Enter Port:', 'AEJEA')
input_size = st.text_input("Enter Size (e.g., 20'):", "40'")
input_quantity = st.number_input('Enter Quantity:', min_value=1)

# Dropdown menu for container type selection
selected_container_type = st.selectbox('Select Container Type:', [''] + list(container_types.keys()))

# Initialize the agents_summary list
agents_summary = []

# Filter data based on input
if selected_container_type:
    if selected_container_type == 'SPECIAL':
        selected_types = container_types['SPECIAL']
    elif selected_container_type == 'DRY':
        selected_types = container_types['DRY']
    else:
        selected_types = []

    filtered_data = df[(df['POL Port'] == input_port) & 
                       (df['Size'] == input_size) & 
                       (df['Activity Mode'] == 'Empty') & 
                       (df['Type'].isin(selected_types))]
else:
    filtered_data = df[(df['POL Port'] == input_port) & 
                       (df['Size'] == input_size) & 
                       (df['Activity Mode'] == 'Empty')]

# Check if there are any available containers
if filtered_data.empty:
    st.write("No containers available for the selected port, size, and type.")
else:
    # Group the data by POL Agent
    grouped_data = filtered_data.groupby('POL Agent').agg({
        'Container #': 'count',  # Count of containers available
        'Ageing Days': 'mean'     # Calculate average ageing days
    }).reset_index()

    # Filter agents that can fulfill the requested quantity
    suitable_agents = grouped_data[grouped_data['Container #'] >= input_quantity]

    if not suitable_agents.empty:
        best_agent = None
        highest_average_ageing = 0
        
        for index, row in suitable_agents.iterrows():
            # Get containers for the current agent
            agent_containers = filtered_data[filtered_data['POL Agent'] == row['POL Agent']]
            # Sort by Ageing Days in descending order
            sorted_containers = agent_containers.sort_values(by='Ageing Days', ascending=False)

            # Check if we can get the top 'input_quantity' containers
            if len(sorted_containers) >= input_quantity:
                # Calculate average ageing days for the selected quantity
                average_ageing = sorted_containers.head(input_quantity)['Ageing Days'].mean()
                
                # Compare with the highest average ageing found
                if average_ageing > highest_average_ageing:
                    highest_average_ageing = average_ageing
                    best_agent = row

        if best_agent is not None:
            st.write(f"Assigned Agent: {best_agent['POL Agent']} - Available Containers: {best_agent['Container #']}")
        else:
            st.write("No agent has sufficient containers to fulfill the request.")
    else:
        # If no single agent can fulfill the request, we need to use multiple agents
        cumulative_containers = 0
        
        # Sort agents by container count in descending order
        sorted_agents = grouped_data.sort_values(by=['Container #'], ascending=False)

        for index, row in sorted_agents.iterrows():
            if cumulative_containers < input_quantity:
                cumulative_containers += row['Container #']
                agent_name = row['POL Agent']
                agents_summary.append({
                    "Agent Name": agent_name,
                    "Available Containers": row['Container #'],
                    "Average Aging": filtered_data[filtered_data['POL Agent'] == agent_name]['Ageing Days'].mean()
                })

        if cumulative_containers >= input_quantity:
            st.write("The following agents can collectively fulfill the request:")
            for agent_detail in agents_summary:
                st.write(f"{agent_detail['Agent Name']} - Average Aging: {agent_detail['Average Aging']:.2f} Days")

            # Prepare detailed report for download
            report_data = []
            for agent in agents_summary:
                # Get all containers for this agent
                agent_data = filtered_data[filtered_data['POL Agent'] == agent['Agent Name']]
                for _, row in agent_data.iterrows():
                    report_data.append(row)

            # Create DataFrame for the report
            report_df = pd.DataFrame(report_data)

            # Generate the CSV file and provide download button
            if not report_df.empty:
                st.download_button(
                    label="Download Report as CSV",
                    data=report_df.to_csv(index=False).encode('utf-8'),
                    file_name='agent_report.csv',
                    mime='text/csv',
                )
        else:
            st.write("No agent has sufficient containers to fulfill the request.")
