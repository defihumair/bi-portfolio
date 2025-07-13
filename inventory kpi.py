import streamlit as st
import pandas as pd
import numpy as np

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

    # ── KPI Tiles ──────────────────────────────────────────────────────────────
    st.markdown("### 🚀 Overall Performance Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Activities", len(filt))
    col2.metric("Excellent (<=2d)", (filt["Performance"] == "Excellent").sum())
    col3.metric("Good (2<d<3)", (filt["Performance"] == "Good").sum())
    col4.metric("Average (3<=d<4)", (filt["Performance"] == "Average").sum())
    col5.metric("Need Improvement (>=4d)", (filt["Performance"] == "Need Improvement").sum())

    # ── Helper ────────────────────────────────────────────────────────────────
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

    # ── Subordinate Table ──────────────────────────────────────────────────────
    st.markdown("### 👥 Subordinate Performance")
    sub_df = filt.groupby("subordinate").agg(
        Total_Activities=("Delay (Days)", "count"),
        Average_Delay=("Delay (Days)", "mean")
    ).round(2).reset_index()
    sub_df["Rating"] = sub_df["Average_Delay"].apply(get_perf_rating)
    st.dataframe(sub_df, use_container_width=True)

    # ── Lead & Region Breakdown ───────────────────────────────────────────────
    for level in ["Lead", "Region"]:
        st.markdown(f"### 👤 {level} Performance")
        df = filt.groupby(level).agg(
            Total_Activities=("Delay (Days)", "count"),
            Average_Delay=("Delay (Days)", "mean")
        ).round(2).reset_index()
        df["Rating"] = df["Average_Delay"].apply(get_perf_rating)
        st.dataframe(df, use_container_width=True)

    # ── Periodic Summaries ─────────────────────────────────────────────────────
    st.markdown("### 📆 Periodic Performance Snapshots")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Monthly")
        month_perf = filt.groupby("Month")["Performance"].value_counts(normalize=True).unstack().fillna(0) * 100
        st.dataframe(month_perf.round(1), use_container_width=True)
    with col_b:
        st.markdown("#### Quarterly")
        qtr_perf = filt.groupby("Quarter")["Performance"].value_counts(normalize=True).unstack().fillna(0) * 100
        st.dataframe(qtr_perf.round(1), use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("#### Weekly")
        wk_perf = filt.groupby("Week")["Performance"].value_counts(normalize=True).unstack().fillna(0) * 100
        st.dataframe(wk_perf.round(1), use_container_width=True)
    with col_d:
        st.markdown("#### Daily (Last 10 Days)")
        daily_perf = filt.groupby("Date")["Performance"].value_counts(normalize=True).unstack().fillna(0) * 100
        st.dataframe(daily_perf.tail(10).round(1), use_container_width=True)

    # ── Raw Table & Export ─────────────────────────────────────────────────────
    st.markdown("### 📋 All Filtered Activity Records")
    st.dataframe(filt, use_container_width=True)

    csv = filt.to_csv(index=False).encode()
    st.download_button("📥 Download Filtered Data as CSV", csv, "filtered_inventory_kpis.csv", "text/csv")

else:
    st.info("⬆️ Please upload both files to begin.")
