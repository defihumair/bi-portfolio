import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="🚢 FIFO Compliance Analyser", layout="wide")
st.title("🚢 FIFO Compliance Analyser – Jebel Ali / MYT")

# ------------------------------
# 1 ▸ Upload & sheet selector
# ------------------------------
uploaded_file = st.file_uploader("📄 Upload Excel file (MYT)", type=["xlsx"])
sheet_name    = st.text_input("Sheet name", value="DRY")

@st.cache_data(show_spinner=False)
def load_data(file, sheet):
    df = pd.read_excel(file, sheet_name=sheet)
    df.columns = df.columns.str.strip()
    df["IN DATE"]  = pd.to_datetime(df["IN DATE"],  errors="coerce")
    df["OUT DATE"] = pd.to_datetime(df["OUT DATE"], errors="coerce")
    return df[df["IN DATE"].notna()]

# ------------------------------
# 2 ▸ FIFO helpers (size + cat + type aware)
# ------------------------------

def fifo_status_and_reason(row, df):
    if pd.isna(row["OUT DATE"]):
        return pd.Series(["In Depot", "Still in depot"])

    mask_same_grp = (
        (df["POL Agent"] == row["POL Agent"]) &
        (df["POL Port"] == row["POL Port"]) &
        (df["Category"]  == row["Category"]) &
        (df["Size"]       == row["Size"]) &
        (df["Type"]       == row["Type"])
    )

    older_in_depot = df[mask_same_grp & (df["IN DATE"] < row["IN DATE"]) & df["OUT DATE"].isna()]

    if older_in_depot.empty:
        return pd.Series(["Yes", "Released in FIFO order"])
    oldest_date = older_in_depot["IN DATE"].min().date()
    return pd.Series(["No", f"Older box still in depot (IN < {oldest_date})"])

@st.cache_data(show_spinner=False)
def analyse_fifo(df):
    df = df.copy()
    df[["FIFO Status", "FIFO Break Reason"]] = df.apply(lambda r: fifo_status_and_reason(r, df), axis=1)

    def summary_fn(sub):
        rel = sub[sub["FIFO Status"].isin(["Yes", "No"])]
        yes = (rel["FIFO Status"] == "Yes").sum()
        no  = (rel["FIFO Status"] == "No").sum()
        pct = round(yes / (yes + no) * 100, 2) if (yes + no) else 0
        return pd.Series({
            "In Depot": (sub["FIFO Status"] == "In Depot").sum(),
            "No": no,
            "Yes": yes,
            "Released": yes + no,
            "FIFO %": pct
        })

    summary = (df.groupby(["POL Port", "POL Agent"], dropna=False)
                 .apply(summary_fn)
                 .reset_index()
                 .sort_values(["POL Port", "FIFO %"], ascending=[True, False]))

    exceptions = df[df["FIFO Status"] == "No"].copy()
    return df, summary, exceptions

# ------------------------------
# 3 ▸ Streamlit logic
# ------------------------------
if uploaded_file:
    try:
        raw_df = load_data(uploaded_file, sheet_name)
    except Exception as e:
        st.error(f"❌ Failed to load sheet: {e}")
        st.stop()

    # --- sidebar filters ---
    st.sidebar.header("🔎 Filters")

    # POL Port multi-select with default all
    all_ports = sorted(raw_df["POL Port"].dropna().unique())
    port_filter = st.sidebar.multiselect("POL Port", all_ports, default=all_ports)

    cat_filter  = st.sidebar.selectbox("Category", sorted(raw_df["Category"].dropna().unique()))
    size_filter = st.sidebar.selectbox("Size", sorted(raw_df["Size"].dropna().unique()))

    # Type options filtered by selected Category + Size
    available_types = raw_df[(raw_df["Category"] == cat_filter) & (raw_df["Size"] == size_filter)]["Type"].dropna().unique()
    type_filter     = st.sidebar.multiselect("Type", sorted(available_types), default=list(sorted(available_types)))

    f_df = raw_df[
        raw_df["POL Port"].isin(port_filter) &
        (raw_df["Category"] == cat_filter) &
        (raw_df["Size"] == size_filter) &
        (raw_df["Type"].isin(type_filter))
    ]

    full_df, summary_df, exceptions_df = analyse_fifo(f_df)

    # --- KPIs ---
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Boxes", len(full_df))
    k2.metric("Released", summary_df["Released"].sum())
    k3.metric("In Depot", summary_df["In Depot"].sum())
    fifo_total = round(summary_df["Yes"].sum() / max(1, summary_df["Yes"].sum()+summary_df["No"].sum()) * 100, 2)
    k4.metric("Overall FIFO %", f"{fifo_total}%")

    tab1, tab2, tab3 = st.tabs(["Agent Summary", "Exceptions", "Raw Data"])

    with tab1:
        st.subheader("Agent‑Port FIFO Summary")
        st.dataframe(summary_df, use_container_width=True)
        st.bar_chart(summary_df.set_index("POL Agent")["FIFO %"])

        dl1 = BytesIO(); summary_df.to_excel(dl1, index=False)
        st.download_button("Download Summary", dl1.getvalue(), file_name="fifo_summary.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab2:
        st.subheader("Containers Breaking FIFO")
        st.dataframe(exceptions_df[["Container #", "POL Port", "POL Agent", "Category", "Size", "Type", "IN DATE", "OUT DATE", "FIFO Break Reason"]], use_container_width=True)
        dl2 = BytesIO(); exceptions_df.to_excel(dl2, index=False)
        st.download_button("Download Exceptions", dl2.getvalue(), file_name="fifo_exceptions.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab3:
        st.subheader("Filtered Raw Data with FIFO Status")
        st.dataframe(full_df, use_container_width=True)
else:
    st.info("👈 Upload an Excel file to begin analysis")
