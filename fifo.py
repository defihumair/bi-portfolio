import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="🚢 FIFO Compliance Analyser", layout="wide")
st.title(":ship: FIFO Compliance Analyser – Jebel Ali / MYT")

# --------------------------------------------------
# 1. Upload Excel file
# --------------------------------------------------
uploaded_file = st.file_uploader("📄 Upload latest MYT Excel (DRY sheet)", type=["xlsx"])
sheet_name = st.text_input("Sheet name", value="DRY")

@st.cache_data(show_spinner=False)
def load_data(file, sheet):
    df = pd.read_excel(file, sheet_name=sheet)
    df.columns = df.columns.str.strip()
    df["IN DATE"] = pd.to_datetime(df["IN DATE"], errors="coerce")
    df["OUT DATE"] = pd.to_datetime(df["OUT DATE"], errors="coerce")
    return df[df["IN DATE"].notna()]

# --------------------------------------------------
# 2. FIFO logic helpers
# --------------------------------------------------

def fifo_status_and_reason(row, df):
    if pd.isna(row["OUT DATE"]):
        return pd.Series(["In Depot", "Still in depot"])

    older_in_depot = df[(df["POL Agent"] == row["POL Agent"]) &
                        (df["IN DATE"] < row["IN DATE"]) &
                        (df["OUT DATE"].isna())]

    if not older_in_depot.empty:
        reason = f"Older box still in depot (IN < {row['IN DATE'].date()})"
        return pd.Series(["No", reason])
    else:
        return pd.Series(["Yes", "Released in FIFO order"])

@st.cache_data(show_spinner=False)
def analyse_fifo(df):
    df = df.copy()
    df[["FIFO Status", "FIFO Break Reason"]] = df.apply(lambda r: fifo_status_and_reason(r, df), axis=1)

    def summary_fn(agent_df):
        released = agent_df[agent_df["FIFO Status"].isin(["Yes", "No"])]
        yes_cnt = (released["FIFO Status"] == "Yes").sum()
        no_cnt = (released["FIFO Status"] == "No").sum()
        fifo_pct = round(yes_cnt / (yes_cnt + no_cnt) * 100, 2) if (yes_cnt + no_cnt) else 0
        return pd.Series({
            "In Depot": (agent_df["FIFO Status"] == "In Depot").sum(),
            "No": no_cnt,
            "Yes": yes_cnt,
            "Total Released": yes_cnt + no_cnt,
            "FIFO %": fifo_pct
        })

    summary = (df.groupby("POL Agent", dropna=False)
                 .apply(summary_fn)
                 .reset_index()
                 .sort_values("FIFO %", ascending=False))

    exceptions = df[df["FIFO Status"] == "No"].copy()

    return df, summary, exceptions

# --------------------------------------------------
# 3. Main App logic
# --------------------------------------------------
if uploaded_file:
    with st.spinner("Processing…"):
        try:
            raw_df = load_data(uploaded_file, sheet_name)
            full_df, summary_df, exceptions_df = analyse_fifo(raw_df)
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🛆 Total Containers", len(full_df))
    col2.metric("🚚 Released", (summary_df["Total Released"].sum()))
    col3.metric("🏷️ In Depot", (summary_df["In Depot"].sum()))
    overall_fifo = round(summary_df["Yes"].sum() / max(1, summary_df["Yes"].sum() + summary_df["No"].sum()) * 100, 2)
    col4.metric("✅ Overall FIFO %", f"{overall_fifo}%")

    tab1, tab2, tab3 = st.tabs(["Agent Summary", "FIFO Exceptions", "Raw Data"])

    with tab1:
        st.subheader("Agent wise FIFO Compliance")
        st.dataframe(summary_df, use_container_width=True)
        st.bar_chart(summary_df.set_index("POL Agent")["FIFO %"])

        buf = BytesIO()
        summary_df.to_excel(buf, index=False)
        st.download_button("📅 Download Summary", buf.getvalue(), file_name="fifo_summary.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab2:
        st.subheader("Containers that Broke FIFO")
        st.dataframe(exceptions_df[["Container #", "POL Agent", "POL Port", "IN DATE", "OUT DATE", "FIFO Break Reason"]], use_container_width=True)
        buf2 = BytesIO()
        exceptions_df.to_excel(buf2, index=False)
        st.download_button("📅 Download Exceptions", buf2.getvalue(), file_name="fifo_exceptions.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab3:
        st.subheader("Raw Data (with FIFO Status)")
        st.dataframe(full_df, use_container_width=True)
else:
    st.info("👈 Upload an Excel file to start!")
