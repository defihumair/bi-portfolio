import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="📈 Inventory KPI Dashboard", layout="wide")

st.title("📦 Inventory Performance KPI Dashboard")
st.markdown("""
Upload your **activity data** file (Excel/CSV) **and** the **POL‑Port mapping** file. This dashboard helps you:
- Track delay between actual activity and system update
- Evaluate performance by person, port, and region
- Drill down with **interactive filters** and see patterns with dynamic charts
""")

# ── File Uploads ────────────────────────────────────────────────────────────────
activity_file = st.file_uploader("📤 Upload Activity Data (Excel/CSV)", type=["xlsx", "xls", "csv"])
map_file = st.file_uploader("🗺️ Upload POL‑Port Mapping", type=["xlsx", "xls", "csv"])

@st.cache_data(show_spinner=False)
def load_data(file):
    if file is None:
        return None
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)

activity_df = load_data(activity_file)
map_df     = load_data(map_file)

if activity_df is not None and map_df is not None:
    # ── Pre‑process ───────────────────────────────────────────────────────────
    activity_df.columns = activity_df.columns.str.strip()
    map_df.columns      = map_df.columns.str.strip()

    activity_df["Activity Date"] = pd.to_datetime(activity_df["Activity Date"], errors="coerce")
    activity_df["System Date"]   = pd.to_datetime(activity_df["System Date"],   errors="coerce")
    activity_df["Delay (Days)"]  = (activity_df["System Date"] - activity_df["Activity Date"]).dt.days

    def classify(delay):
        if pd.isna(delay):           return "Missing"
        if delay <= 2:               return "Excellent"
        elif delay < 3:              return "Good"
        elif delay < 4:              return "Average"
        else:                        return "Need Improvement"

    activity_df["Performance"] = activity_df["Delay (Days)"].apply(classify)

    merged = activity_df.merge(map_df, how="left", on="POL Port")
    merged["Month"]   = merged["Activity Date"].dt.to_period("M")
    merged["Quarter"] = merged["Activity Date"].dt.to_period("Q")
    merged["Week"]    = merged["Activity Date"].dt.isocalendar().week
    merged["Date"]    = merged["Activity Date"].dt.date
    merged["WeekStart"] = merged["Activity Date"] - pd.to_timedelta(merged["Activity Date"].dt.weekday, unit="d")
    merged["Week Range"] = merged["WeekStart"].dt.strftime('%d %b') + " - " + (merged["WeekStart"] + pd.Timedelta(days=6)).dt.strftime('%d %b')

    # ── Sidebar Filters ───────────────────────────────────────────────────────
    st.sidebar.header("🔍 Filters")
    region_f = st.sidebar.multiselect("Region",      sorted(merged["Region"].dropna().unique()))
    lead_f   = st.sidebar.multiselect("Lead",        sorted(merged["Lead"].dropna().unique()))
    sub_f    = st.sidebar.multiselect("Subordinate", sorted(merged["subordinate"].dropna().unique()))
    port_f   = st.sidebar.multiselect("POL Port",    sorted(merged["POL Port"].dropna().unique()))
    dates    = st.sidebar.date_input("Date Range",   [])

    filt = merged.copy()
    if region_f: filt = filt[filt["Region"].isin(region_f)]
    if lead_f:   filt = filt[filt["Lead"].isin(lead_f)]
    if sub_f:    filt = filt[filt["subordinate"].isin(sub_f)]
    if port_f:   filt = filt[filt["POL Port"].isin(port_f)]
    if len(dates)==2:
        filt = filt[(filt["Activity Date"]>=pd.to_datetime(dates[0])) & (filt["Activity Date"]<=pd.to_datetime(dates[1]))]

    # ── Helpers ───────────────────────────────────────────────────────────────
    def rating(avg):
        if pd.isna(avg): return "Missing"
        if avg <=2:      return "Excellent"
        if avg <3:       return "Good"
        if avg <4:       return "Average"
        return "Need Improvement"

    # ── KPI Tiles ─────────────────────────────────────────────────────────────
    st.markdown("### 🚀 Overall Performance")
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("Total",               len(filt))
    col2.metric("Excellent",          (filt["Performance"]=="Excellent").sum())
    col3.metric("Good",               (filt["Performance"]=="Good").sum())
    col4.metric("Average",            (filt["Performance"]=="Average").sum())
    col5.metric("Need Improve",       (filt["Performance"]=="Need Improvement").sum())

    # ── Subordinate Table ─────────────────────────────────────────────────────
    st.markdown("### 👥 Subordinate Performance")
    sub_tbl = (filt.groupby("subordinate")
                     .agg(Total=("Delay (Days)","count"), AvgDelay=("Delay (Days)","mean"))
                     .round(2).reset_index())
    sub_tbl["Rating"] = sub_tbl["AvgDelay"].apply(rating)
    st.dataframe(sub_tbl,use_container_width=True)
      
    # ── POL Port Table & Chart ────────────────────────────────────────────────
    st.markdown("### 🧭 POL Port Performance")
    port_tbl = (filt.groupby("POL Port")
                     .agg(Total=("Delay (Days)","count"), AvgDelay=("Delay (Days)","mean"))
                     .round(2).reset_index())
    port_tbl["Rating"] = port_tbl["AvgDelay"].apply(rating)
    st.dataframe(port_tbl,use_container_width=True)

    # Interactive bar chart for AvgDelay by port
    if not port_tbl.empty:
        bar_fig = px.bar(port_tbl, x="POL Port", y="AvgDelay", color="Rating",
                         title="Average Delay by POL Port", labels={"AvgDelay":"Avg Delay (Days)"})
        bar_fig.update_layout(xaxis_tickangle=-45, height=400)
        st.plotly_chart(bar_fig,use_container_width=True)

    # ── Subordinate + Port Table & Heatmap ────────────────────────────────────
    st.markdown("### 🧾 Subordinate vs POL Port Performance")
    combo = (filt.groupby(["subordinate","POL Port"])
                   .agg(AvgDelay=("Delay (Days)","mean"))
                   .round(2).reset_index())
    st.dataframe(combo,use_container_width=True)

    if not combo.empty:
        pivot = combo.pivot(index="subordinate", columns="POL Port", values="AvgDelay")
        heat = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="Blues",
                         title="Average Delay Heatmap (Subordinate vs POL Port)")
        heat.update_layout(height=500)
        st.plotly_chart(heat,use_container_width=True)

    # ── Daily Trend Chart ─────────────────────────────────────────────────────
    st.markdown("### 📊 Daily Average Delay Trend")
    trend = filt.groupby("Date")["Delay (Days)"].mean().round(2).reset_index()
    if not trend.empty:
        line = px.line(trend, x="Date", y="Delay (Days)", markers=True,
                       title="Daily Average Delay")
        line.update_layout(yaxis_title="Avg Delay (Days)", height=350)
        st.plotly_chart(line,use_container_width=True)
else:
    st.info("⬆️ Upload both files to begin.")
