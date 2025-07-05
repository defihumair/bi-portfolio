# vessel.py - Advanced Vessel Movement Analyzer with Deep Insights

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
from io import BytesIO

# Load data
file_path = 'Ametist.xlsx'
df = pd.read_excel(file_path)
df = df[['Vessel', 'Port of loading', 'Unloading port', 'Departure', 'Arrival']]
df.dropna(inplace=True)

# Convert dates
df['Departure'] = pd.to_datetime(df['Departure'], errors='coerce')
df['Arrival'] = pd.to_datetime(df['Arrival'], errors='coerce')

# Port coordinates
port_coords = {
    'NOVOROSSIYSK': (44.7239, 37.7695), 'MERSIN': (36.7990, 34.6400), 'BEIRUT': (33.9017, 35.4866),
    'ALEXANDRIA (OLDPORT)': (31.2001, 29.9187), 'AMBARLI': (40.9541, 28.7335), 'GEBZE': (40.7976, 29.4304),
    'ASHDOD': (31.8044, 34.6553), 'HAIFA': (32.7940, 34.9896), 'EL DEKHEILA': (31.1333, 29.8667),
    'SANKO': (36.8, 34.6), 'DAMIETTA': (31.4167, 31.8167)
}

st.set_page_config(layout="wide")
st.title("🚢 Vessel Route Analyzer & Strategic Planner")

# Sidebar Filters
vessels = sorted(df['Vessel'].unique())
selected_vessels = st.sidebar.multiselect("🔍 Select Vessel(s)", vessels, default=vessels[:1])
date_range = st.sidebar.date_input("📅 Date Range", [df['Departure'].min(), df['Arrival'].max()])

# Filtered Data
df_filtered = df[df['Vessel'].isin(selected_vessels)]
df_filtered = df_filtered[(df_filtered['Departure'] >= pd.to_datetime(date_range[0])) & (df_filtered['Arrival'] <= pd.to_datetime(date_range[1]))]

# SECTION 1: Round-trip duration from origin
st.header("🔄 Round-trip Analysis")
for vessel in selected_vessels:
    st.subheader(f"⛴ {vessel} Round-trip")
    df_vessel = df_filtered[df_filtered['Vessel'] == vessel]
    df_novo = df_vessel[(df_vessel['Port of loading'] == 'NOVOROSSIYSK') | (df_vessel['Unloading port'] == 'NOVOROSSIYSK')].sort_values('Departure')
    if len(df_novo) >= 2:
        start = df_novo.iloc[0]['Departure']
        end = df_novo.iloc[-1]['Arrival']
        duration = (end - start).days
        st.success(f"Round-trip from NOVOROSSIYSK took **{duration} days**.")
    else:
        st.warning("Not enough NOVOROSSIYSK data for round-trip calculation.")

# SECTION 2: Interactive Route Map
st.header("🗺️ Route Map")
fig = go.Figure()
for _, row in df_filtered.iterrows():
    origin, dest = row['Port of loading'], row['Unloading port']
    if origin in port_coords and dest in port_coords:
        lat0, lon0 = port_coords[origin]
        lat1, lon1 = port_coords[dest]
        fig.add_trace(go.Scattermapbox(
            lat=[lat0, lat1], lon=[lon0, lon1], mode="lines+markers",
            line=dict(width=2),
            hoverinfo="text", text=f"{row['Vessel']}\n{origin} → {dest}<br>{row['Departure'].date()} to {row['Arrival'].date()}"
        ))
for port, (lat, lon) in port_coords.items():
    fig.add_trace(go.Scattermapbox(lat=[lat], lon=[lon], mode='markers+text',
        marker=dict(size=8, color='red'), text=[port], textposition='top center'))
fig.update_layout(mapbox=dict(style='open-street-map', center=dict(lat=34.5, lon=35), zoom=4), margin=dict(l=0, r=0, t=0, b=0))
st.plotly_chart(fig, use_container_width=True)

# SECTION 3: Port Call Frequency
st.header("📊 Port Call Frequency")
call_freq = df_filtered.groupby(['Unloading port', 'Vessel']).size().reset_index(name='Calls')
fig_bar = px.bar(call_freq, x='Unloading port', y='Calls', color='Vessel', title='Port Call Frequency by Vessel')
st.plotly_chart(fig_bar, use_container_width=True)

# SECTION 4: Intersection Ports
st.header("🧭 Intersection Ports")
intersections = df_filtered.groupby('Unloading port')['Vessel'].nunique().reset_index(name='Unique Vessels')
fig_ports = px.scatter(intersections, x='Unloading port', y='Unique Vessels', size='Unique Vessels', color='Unique Vessels', title='Ports Used by Multiple Vessels')
st.plotly_chart(fig_ports, use_container_width=True)

# SECTION 5: Strategic Port Ranking
st.header("🏆 Important Ports")
df_ports = pd.concat([df_filtered[['Port of loading']], df_filtered[['Unloading port']].rename(columns={'Unloading port': 'Port of loading'})])
port_rank = df_ports['Port of loading'].value_counts().reset_index()
port_rank.columns = ['Port', 'Frequency']
fig_rank = px.bar(port_rank, x='Port', y='Frequency', title='Most Frequently Used Ports')
st.plotly_chart(fig_rank, use_container_width=True)

# SECTION 6: Network Graph
st.header("🌐 Route Network Graph")
G = nx.from_pandas_edgelist(df_filtered, 'Port of loading', 'Unloading port', create_using=nx.DiGraph())
pos = nx.spring_layout(G)
fig_net = go.Figure()
for edge in G.edges():
    fig_net.add_trace(go.Scatter(x=[pos[edge[0]][0], pos[edge[1]][0]], y=[pos[edge[0]][1], pos[edge[1]][1]],
                                 mode='lines', line=dict(width=1, color='gray')))
for node in G.nodes():
    fig_net.add_trace(go.Scatter(x=[pos[node][0]], y=[pos[node][1]], text=[node], mode='markers+text',
                                 marker=dict(size=10), textposition='top center'))
fig_net.update_layout(showlegend=False, title='Port Connection Graph', margin=dict(l=0, r=0, t=30, b=0))
st.plotly_chart(fig_net, use_container_width=True)
