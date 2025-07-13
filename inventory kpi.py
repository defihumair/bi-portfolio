import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Inventory KPI Dashboard", layout="wide")

st.title("📦 Inventory Performance KPI Dashboard")
st.markdown("Upload your **activity data** file (Excel/CSV) **and** the **POL‑Port mapping** file. The app will calculate delay‑based KPIs, classify performance, and let you drill down by Region, Lead, Subordinate, or Port.")

# ── File Uploads ────────────────────────────────────────────────────────────────
activity_file = st.file_uploader("Activity Data (Excel or CSV)", type=["xlsx", "xls", "csv"])
map_file = st.file_uploader("POL Port Mapping (Excel or CSV)", type=["xlsx", "xls", "csv"])

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
    # ── Standardise column names ────────────────────────────────────────────────
    activity_df.columns = activity_df.columns.str.strip()
    map_df.columns = map_df.columns.str.strip()

    # ── Calculate Delay & Performance Bucket ───────────────────────────────────
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

    # ── Merge with Mapping ──────────────────────────────────────────────────────
    merged = activity_df.merge(map_df, how="left", left_on="POL Port", right_on="POL Port")

    # ── Add Period Columns ──────────────────────────────────────────────────────
    merged["Month"] = merged["Activity Date"].dt.to_period("M")
    merged["Week"] = merged["Activity Date"].dt.isocalendar().week
    merged["Date"] = merged["Activity Date"].dt.date

    # ── Sidebar Filters ────────────────────────────────────────────────────────
    st.sidebar.header("🔍 Filters")
    region_sel = st.sidebar.multiselect("Region", sorted(merged["Region"].dropna().unique()))
    lead_sel = st.sidebar.multiselect("Lead", sorted(merged["Lead"].dropna().unique()))
    sub_sel = st.sidebar.multiselect("Subordinate", sorted(merged["subordinate"].dropna().unique()))
    port_sel = st.sidebar.multiselect("POL Port", sorted(merged["POL Port"].dropna().unique()))

    filt = merged.copy()
    if region_sel:
        filt = filt[filt["Region"].isin(region_sel)]
    if lead_sel:
        filt = filt[filt["Lead"].isin(lead_sel)]
    if sub_sel:
        filt = filt[filt["subordinate"].isin(sub_sel)]
    if port_sel:
        filt = filt[filt["POL Port"].isin(port_sel)]

    # ── KPI Tiles ──────────────────────────────────────────────────────────────
    total = len(filt)
    excellent = (filt["Performance"] == "Excellent").sum()
    good = (filt["Performance"] == "Good").sum()
    average = (filt["Performance"] == "Average").sum()
    need_imp = (filt["Performance"] == "Need Improvement").sum()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Activities", f"{total}")
    col2.metric("Excellent (<=2d)", f"{excellent}")
    col3.metric("Good (2<d<3)", f"{good}")
    col4.metric("Average (3<=d<4)", f"{average}")
    col5.metric("Need Improve (>=4d)", f"{need_imp}")

    # ── Breakdown Tables ───────────────────────────────────────────────────────
    st.subheader("Breakdown by Subordinate")
    sub_df = filt.groupby("subordinate").agg(
        Total_Activities=("Delay (Days)", "count"),
        Average_Delay=("Delay (Days)", "mean")
    ).round(2).reset_index()
    perf_counts = filt.groupby("subordinate")["Performance"].value_counts().unstack(fill_value=0)
    sub_table = sub_df.join(perf_counts, on="subordinate")
    st.dataframe(sub_table.reset_index(drop=True), use_container_width=True)

    st.subheader("Breakdown by Lead")
    lead_df = filt.groupby("Lead").agg(
        Total_Activities=("Delay (Days)", "count"),
        Average_Delay=("Delay (Days)", "mean")
    ).round(2).reset_index()
    lead_counts = filt.groupby("Lead")["Performance"].value_counts().unstack(fill_value=0)
    lead_table = lead_df.join(lead_counts, on="Lead")
    st.dataframe(lead_table.reset_index(drop=True), use_container_width=True)

    st.subheader("Breakdown by Region")
    region_df = filt.groupby("Region").agg(
        Total_Activities=("Delay (Days)", "count"),
        Average_Delay=("Delay (Days)", "mean")
    ).round(2).reset_index()
    region_counts = filt.groupby("Region")["Performance"].value_counts().unstack(fill_value=0)
    region_table = region_df.join(region_counts, on="Region")
    st.dataframe(region_table.reset_index(drop=True), use_container_width=True)

    # ── Monthly, Weekly, Daily KPIs ────────────────────────────────────────────
    st.subheader("📅 Monthly Average Performance")
    monthly_perf = (
        filt.groupby("Month")["Performance"]
        .value_counts(normalize=True)
        .unstack()
        .fillna(0) * 100
    ).round(1)
    st.dataframe(monthly_perf, use_container_width=True)

    st.subheader("📆 Weekly Average Performance")
    weekly_perf = (
        filt.groupby("Week")["Performance"]
        .value_counts(normalize=True)
        .unstack()
        .fillna(0) * 100
    ).round(1)
    st.dataframe(weekly_perf, use_container_width=True)

    st.subheader("📊 Daily Average Performance (Last 10 Days)")
    daily_perf = (
        filt.groupby("Date")["Performance"]
        .value_counts(normalize=True)
        .unstack()
        .fillna(0) * 100
    ).round(1)
    st.dataframe(daily_perf.tail(10), use_container_width=True)

    # ── Detail Grid ────────────────────────────────────────────────────────────
    st.subheader("Detailed Activity Records")
    st.dataframe(filt, use_container_width=True)

    # ── Export Option ──────────────────────────────────────────────────────────
    csv = filt.to_csv(index=False).encode()
    st.download_button("Download Filtered Data as CSV", csv, "filtered_inventory_kpis.csv", "text/csv")

else:
    st.info("⬆️ Upload both files to begin analysis.")
