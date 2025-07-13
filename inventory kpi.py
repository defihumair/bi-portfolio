import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="📈 Inventory KPI Dashboard", layout="wide")

st.title("📦 Inventory Performance KPI Dashboard")
st.markdown("""
Upload your **activity data** file (Excel/CSV) **and** the **POL‑Port mapping** file. This dashboard helps you:
- Track delay between actual activity and system update
- Evaluate performance of each team member and department
- Filter KPIs by Region, Lead, Subordinate, Port, and now also by **Date Range**, **Week**, **Month**, or **Quarter**
""")

# ── File Uploads ────────────────────────────────────────────────────────────────
activity_file = st.file_uploader("📤 Upload Activity Data (Excel/CSV)", type=["xlsx", "xls", "csv"])
map_file = st.file_uploader("🗺️ Upload POL-Port Mapping", type=["xlsx", "xls", "csv"])

@st.cache_data(show_spinner=False)
def load_data(file):
    if file is None:
        return None
    if file.name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    return pd.read_csv(file)

activity_df = load_data(activity_file)
map_df = load_data(map_file)

if activity_df is not None and map_df is not None:
    activity_df.columns = activity_df.columns.str.strip()
    map_df.columns = map_df.columns.str.strip()

    activity_df["Activity Date"] = pd.to_datetime(activity_df["Activity Date"], errors="coerce")
    activity_df["System Date"] = pd.to_datetime(activity_df["System Date"], errors="coerce")
    activity_df["Delay (Days)"] = (activity_df["System Date"] - activity_df["Activity Date"]).dt.days

    def classify(delay):
        if pd.isna(delay):
            return "Missing"
        if delay <= 2:
            return "Excellent"
        elif delay < 3:
            return "Good"
        elif delay < 4:
            return "Average"
        else:
            return "Need Improvement"

    activity_df["Performance"] = activity_df["Delay (Days)"].apply(classify)

    merged = activity_df.merge(map_df, how="left", on="POL Port")
    merged["Month"] = merged["Activity Date"].dt.to_period("M")
    merged["Week"] = merged["Activity Date"].dt.isocalendar().week
    merged["Quarter"] = merged["Activity Date"].dt.to_period("Q")
    merged["Date"] = merged["Activity Date"].dt.date
    merged["Week Start"] = merged["Activity Date"] - pd.to_timedelta(merged["Activity Date"].dt.weekday, unit='d')
    merged["Week Range"] = merged["Week Start"].dt.strftime('%d %b') + " - " + (merged["Week Start"] + pd.Timedelta(days=6)).dt.strftime('%d %b')

    st.sidebar.header("🔍 Filter Criteria")
    region_sel = st.sidebar.multiselect("🌍 Region", sorted(merged["Region"].dropna().unique()))
    lead_sel = st.sidebar.multiselect("👤 Lead", sorted(merged["Lead"].dropna().unique()))
    sub_sel = st.sidebar.multiselect("👥 Subordinate", sorted(merged["subordinate"].dropna().unique()))
    port_sel = st.sidebar.multiselect("🛳️ POL Port", sorted(merged["POL Port"].dropna().unique()))
    date_range = st.sidebar.date_input("📅 Select Activity Date Range", [])

    filt = merged.copy()
    if region_sel:
        filt = filt[filt["Region"].isin(region_sel)]
    if lead_sel:
        filt = filt[filt["Lead"].isin(lead_sel)]
    if sub_sel:
        filt = filt[filt["subordinate"].isin(sub_sel)]
    if port_sel:
        filt = filt[filt["POL Port"].isin(port_sel)]
    if len(date_range) == 2:
        filt = filt[(filt["Activity Date"] >= pd.to_datetime(date_range[0])) & (filt["Activity Date"] <= pd.to_datetime(date_range[1]))]

    st.markdown("### 🚀 Overall Performance Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Activities", len(filt))
    col2.metric("Excellent (<=2d)", (filt["Performance"] == "Excellent").sum())
    col3.metric("Good (2<d<3)", (filt["Performance"] == "Good").sum())
    col4.metric("Average (3<=d<4)", (filt["Performance"] == "Average").sum())
    col5.metric("Need Improvement (>=4d)", (filt["Performance"] == "Need Improvement").sum())

    def get_perf_rating(avg_delay):
        if pd.isna(avg_delay):
            return "Missing"
        elif avg_delay <= 2:
            return "Excellent"
        elif avg_delay < 3:
            return "Good"
        elif avg_delay < 4:
            return "Average"
        else:
            return "Need Improvement"

    st.markdown("### 👥 Subordinate Performance")
    sub_df = filt.groupby("subordinate").agg(
        Total_Activities=("Delay (Days)", "count"),
        Average_Delay=("Delay (Days)", "mean")
    ).round(2).reset_index()
    sub_df["Rating"] = sub_df["Average_Delay"].apply(get_perf_rating)
    st.dataframe(sub_df, use_container_width=True)

    for level in ["Lead", "Region"]:
        st.markdown(f"### 👤 {level} Performance")
        df = filt.groupby(level).agg(
            Total_Activities=("Delay (Days)", "count"),
            Average_Delay=("Delay (Days)", "mean")
        ).round(2).reset_index()
        df["Rating"] = df["Average_Delay"].apply(get_perf_rating)
        st.dataframe(df, use_container_width=True)

    st.markdown("### 📆 Periodic Performance Snapshots")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Monthly")
        monthly = filt.groupby("Month")["Delay (Days)"].mean().round(2).reset_index()
        monthly["Rating"] = monthly["Delay (Days)"].apply(get_perf_rating)
        st.dataframe(monthly.rename(columns={"Delay (Days)": "Avg Delay"}), use_container_width=True)
    with col_b:
        st.markdown("#### Quarterly")
        qtr = filt.groupby("Quarter")["Delay (Days)"].mean().round(2).reset_index()
        qtr["Rating"] = qtr["Delay (Days)"].apply(get_perf_rating)
        st.dataframe(qtr.rename(columns={"Delay (Days)": "Avg Delay"}), use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("#### Weekly Summary (e.g. 01 Jun - 07 Jun)")
        week_label = filt.groupby("Week Range")["Delay (Days)"].mean().round(2).reset_index()
        week_label["Rating"] = week_label["Delay (Days)"].apply(get_perf_rating)
        st.dataframe(week_label.rename(columns={"Delay (Days)": "Avg Delay"}), use_container_width=True)
    with col_d:
        st.markdown("#### Daily Summary (Scroll All)")
        daily = filt.groupby("Date")["Delay (Days)"].mean().round(2).reset_index()
        daily["Rating"] = daily["Delay (Days)"].apply(get_perf_rating)
        st.dataframe(daily.rename(columns={"Delay (Days)": "Avg Delay"}), use_container_width=True, height=500)

    st.markdown("### 📊 Daily Average Delay Chart")
    chart_data = filt.groupby("Date")["Delay (Days)"].mean().round(2).reset_index()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(chart_data["Date"], chart_data["Delay (Days)"], marker="o", linestyle="-", color="steelblue")
    ax.set_title("Daily Average Delay Trend", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Avg Delay (Days)")
    ax.grid(True)
    st.pyplot(fig)

    st.markdown("### 📄 Summary Report PDF Download")
    st.warning("⚠️ This feature is under development. You'll be able to export a boss-ready PDF soon.")

else:
    st.info("⬆️ Please upload both files to begin.")
