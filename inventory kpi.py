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

    # ── Performance Breakdown Tables ───────────────────────────────────────────
    st.subheader("Breakdown by Subordinate")
    st.dataframe(
        filt.groupby("subordinate")["Performance"].value_counts().unstack(fill_value=0).reset_index(),
        use_container_width=True,
    )

    st.subheader("Breakdown by Lead")
    st.dataframe(
        filt.groupby("Lead")["Performance"].value_counts().unstack(fill_value=0).reset_index(),
        use_container_width=True,
    )

    st.subheader("Breakdown by Region")
    st.dataframe(
        filt.groupby("Region")["Performance"].value_counts().unstack(fill_value=0).reset_index(),
        use_container_width=True,
    )

    # ── Detail Grid ────────────────────────────────────────────────────────────
    st.subheader("Detailed Activity Records")
    st.dataframe(filt, use_container_width=True)

    # ── Export Option ──────────────────────────────────────────────────────────
    csv = filt.to_csv(index=False).encode()
    st.download_button("Download Filtered Data as CSV", csv, "filtered_inventory_kpis.csv", "text/csv")

else:
    st.info("⬆️ Upload both files to begin analysis.")
