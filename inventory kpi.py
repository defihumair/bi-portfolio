import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="📈 Inventory KPI Dashboard", layout="wide")

st.title("📦 Inventory Performance KPI Dashboard")
st.markdown("""
Upload your **activity data** file (Excel/CSV) and **POL-Port mapping** file.

This dashboard helps you:
- Track delay between physical activity and system update
- Evaluate performance by Person, Port, Region, Lead
- Filter by Company, Date Range, Region, Subordinate, Port
- Visualize average delays with interactive charts and heatmaps
""")

# ── File Uploads ─────────────────────────────────────────────
activity_file = st.file_uploader("📤 Upload Activity Data", type=["xlsx", "xls", "csv"])
map_file = st.file_uploader("🗺️ Upload POL-Port Mapping", type=["xlsx", "xls", "csv"])

@st.cache_data(show_spinner=False)
def load_data(file):
    if file is None:
        return None
    return pd.read_excel(file) if file.name.endswith(('xlsx', 'xls')) else pd.read_csv(file)

activity_df = load_data(activity_file)
map_df = load_data(map_file)

if activity_df is not None and map_df is not None:
    # ── Clean and Prepare ─────────────────────────────────────
    activity_df.columns = activity_df.columns.str.strip()
    map_df.columns = map_df.columns.str.strip()

    activity_df["Activity Date"] = pd.to_datetime(activity_df["Activity Date"], errors="coerce")
    activity_df["System Date"] = pd.to_datetime(activity_df["System Date"], errors="coerce")
    activity_df["Delay (Days)"] = (activity_df["System Date"] - activity_df["Activity Date"]).dt.days

    def classify(delay):
        if pd.isna(delay): return "Missing"
        if delay <= 2: return "Excellent"
        elif delay < 3: return "Good"
        elif delay < 4: return "Average"
        else: return "Need Improvement"

    activity_df["Performance"] = activity_df["Delay (Days)"].apply(classify)

    # ── Merge mapping with Company column ──────────────────────
    merged = activity_df.merge(map_df, how="left", on=["Company", "POL Port"])
    
    # Handle potential Company_x / Company_y issue
    if "Company_y" in merged.columns:
        merged.rename(columns={"Company_y": "Company"}, inplace=True)
    elif "Company_x" in merged.columns:
        merged.rename(columns={"Company_x": "Company"}, inplace=True)

    merged["Month"] = merged["Activity Date"].dt.to_period("M")
    merged["Quarter"] = merged["Activity Date"].dt.to_period("Q")
    merged["Week"] = merged["Activity Date"].dt.isocalendar().week
    merged["Date"] = merged["Activity Date"].dt.date
    merged["WeekStart"] = merged["Activity Date"] - pd.to_timedelta(merged["Activity Date"].dt.weekday, unit="d")
    merged["Week Range"] = merged["WeekStart"].dt.strftime('%d %b') + " - " + (merged["WeekStart"] + pd.Timedelta(days=6)).dt.strftime('%d %b')

    # ── Filters ───────────────────────────────────────────────
    st.sidebar.header("🔍 Filters")
    company_f = st.sidebar.multiselect("🏢 Company", sorted(merged["Company"].dropna().unique()))
    region_f = st.sidebar.multiselect("🌍 Region", sorted(merged["Region"].dropna().unique()))
    lead_f = st.sidebar.multiselect("👤 Lead", sorted(merged["Lead"].dropna().unique()))
    sub_f = st.sidebar.multiselect("👥 Subordinate", sorted(merged["subordinate"].dropna().unique()))
    port_f = st.sidebar.multiselect("🛳️ POL Port", sorted(merged["POL Port"].dropna().unique()))
    dates = st.sidebar.date_input("📅 Activity Date Range", [])

    # Apply filters
    filt = merged.copy()
    if company_f: filt = filt[filt["Company"].isin(company_f)]
    if region_f: filt = filt[filt["Region"].isin(region_f)]
    if lead_f: filt = filt[filt["Lead"].isin(lead_f)]
    if sub_f: filt = filt[filt["subordinate"].isin(sub_f)]
    if port_f: filt = filt[filt["POL Port"].isin(port_f)]
    if len(dates) == 2:
        filt = filt[(filt["Activity Date"] >= pd.to_datetime(dates[0])) & (filt["Activity Date"] <= pd.to_datetime(dates[1]))]

    def get_rating(avg):
        if pd.isna(avg): return "Missing"
        elif avg <= 2: return "Excellent"
        elif avg < 3: return "Good"
        elif avg < 4: return "Average"
        else: return "Need Improvement"

    
    # ── Summary KPIs ──────────────────────────────────────────
    st.markdown("### 🚀 Overall Performance Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Activities", len(filt))
    col2.metric("Excellent (<=2d)", (filt["Performance"] == "Excellent").sum())
    col3.metric("Good (2<d<3)", (filt["Performance"] == "Good").sum())
    col4.metric("Average (3<=d<4)", (filt["Performance"] == "Average").sum())
    col5.metric("Need Improve (>=4d)", (filt["Performance"] == "Need Improvement").sum())

    # ── Subordinate Table ─────────────────────────────────────
    st.markdown("### 👥 Subordinate Performance")
    sub_tbl = filt.groupby("subordinate").agg(
        Total_Activities=("Delay (Days)", "count"),
        Avg_Delay=("Delay (Days)", "mean")
    ).round(2).reset_index()
    sub_tbl["Rating"] = sub_tbl["Avg_Delay"].apply(get_rating)
    st.dataframe(sub_tbl, use_container_width=True)

    # ── Lead & Region Performance ─────────────────────────────
    for level in ["Lead", "Region"]:
        st.markdown(f"### 👤 {level} Performance")
        df = filt.groupby(level).agg(
            Total_Activities=("Delay (Days)", "count"),
            Average_Delay=("Delay (Days)", "mean")
        ).round(2).reset_index()
        df["Rating"] = df["Average_Delay"].apply(get_rating)
        st.dataframe(df, use_container_width=True)

    # ── POL Port Performance ─────────────────────────────────
    st.markdown("### 🧭 POL Port Performance — Average delay & rating")
    port_tbl = filt.groupby("POL Port").agg(
        Total_Activities=("Delay (Days)", "count"),
        Avg_Delay=("Delay (Days)", "mean")
    ).round(2).reset_index()
    port_tbl["Rating"] = port_tbl["Avg_Delay"].apply(get_rating)

    st.dataframe(port_tbl, use_container_width=True)

    # Define custom colors for ratings
    rating_colors = {
        "Excellent": "green",
        "Good": "yellowgreen",
        "Average": "orange",
        "Need Improvement": "red",
        "Missing": "gray"
    }

    # Bar chart with custom colors
    fig = px.bar(
        port_tbl, 
        x="POL Port", 
        y="Avg_Delay", 
        color="Rating",
        color_discrete_map=rating_colors,
        title="Average Delay by POL Port", 
        labels={"Avg_Delay": "Avg Delay (Days)"}
    )
    fig.update_layout(xaxis_tickangle=-45, height=400)
    st.plotly_chart(fig, use_container_width=True)

    # ── Subordinate vs POL Port Heatmap ──────────────────────
    st.markdown("### 🔥 Average Delay Heatmap (Subordinate vs POL Port)")
    combo = filt.groupby(["subordinate", "POL Port"]).agg(
        Avg_Delay=("Delay (Days)", "mean")
    ).round(2).reset_index()
    if not combo.empty:
        pivot = combo.pivot(index="subordinate", columns="POL Port", values="Avg_Delay")
        heat = px.imshow(pivot, text_auto=True, aspect="auto", color_continuous_scale="Blues",
                         title="Subordinate vs POL Port — Avg Delay Heatmap")
        st.plotly_chart(heat, use_container_width=True)

    # ── Daily Trend Analysis with Insights ─────────────────────────────────────
st.markdown("### 📊 Daily Average Delay Trend with Insights")

# Calculate daily average delay
trend = filt.groupby("Date")["Delay (Days)"].mean().round(2).reset_index()

if not trend.empty:
    # 1. Detect peaks (top 10% delay days)
    threshold = trend["Delay (Days)"].quantile(0.9)
    peaks = trend[trend["Delay (Days)"] >= threshold]

    # 2. Weekday analysis
    trend["Weekday"] = pd.to_datetime(trend["Date"]).dt.day_name()
    weekday_avg = trend.groupby("Weekday")["Delay (Days)"].mean().round(2).reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )

    # 3. Plot daily delay trend with peaks
    line = px.line(trend, x="Date", y="Delay (Days)", markers=True,
                   title="Daily Avg Delay Trend with Peaks",
                   labels={"Delay (Days)": "Avg Delay"})

    for i, row in peaks.iterrows():
        line.add_annotation(x=row["Date"], y=row["Delay (Days)"],
                            text="Peak", showarrow=True, arrowhead=2, 
                            yshift=10, font=dict(color="red"))

    st.plotly_chart(line, use_container_width=True)

    # 4. Weekday bar chart to see patterns
    bar = px.bar(weekday_avg, x=weekday_avg.index, y="Delay (Days)",
                 title="Average Delay by Weekday",
                 labels={"Weekday": "Day", "Delay (Days)": "Avg Delay"})
    st.plotly_chart(bar, use_container_width=True)

    # 5. Insights summary
    st.subheader("🔎 Insights")
    st.markdown(f"""
    - **Peak Delay Days**: {', '.join(peaks['Date'].astype(str).tolist())}
    - **Worst Weekday**: {weekday_avg.idxmax()} (Avg Delay: {weekday_avg.max()} Days)
    - **Best Weekday**: {weekday_avg.idxmin()} (Avg Delay: {weekday_avg.min()} Days)
    """)
else:
    st.warning("No data available for daily trend analysis.")
    
# ── Additional KPI Visualizations ──────────────────────────────
st.markdown("## 📊 Additional KPI Insights")

# 1️⃣ Delay Distribution (Histogram + Boxplot)
st.markdown("### ⏱️ Delay Distribution")
if not filt.empty:
    hist = px.histogram(
        filt, 
        x="Delay (Days)", 
        nbins=20, 
        title="Distribution of Delay Days",
        labels={"Delay (Days)": "Delay in Days"},
        color_discrete_sequence=["teal"]
    )
    st.plotly_chart(hist, use_container_width=True)

    box = px.box(
        filt,
        y="Delay (Days)",
        points="outliers",
        title="Boxplot of Delays — Identify Outliers",
        labels={"Delay (Days)": "Delay in Days"}
    )
    st.plotly_chart(box, use_container_width=True)
else:
    st.warning("No data available for Delay Distribution.")

# 2️⃣ Workload vs Performance (Total Activities vs Avg Delay)
st.markdown("### ⚡ Workload vs Performance")
if not filt.empty:
    workload_df = filt.groupby("subordinate").agg(
        Total_Activities=("Delay (Days)", "count"),
        Avg_Delay=("Delay (Days)", "mean")
    ).reset_index()

    scatter = px.scatter(
        workload_df, x="Total_Activities", y="Avg_Delay",
        size="Total_Activities", color="Avg_Delay",
        color_continuous_scale="RdYlGn_r",
        title="Workload vs Average Delay",
        labels={"Total_Activities": "Number of Activities", "Avg_Delay": "Average Delay (Days)"},
        hover_data=["subordinate"]
    )
    st.plotly_chart(scatter, use_container_width=True)
else:
    st.warning("No data available for Workload vs Performance.")

# 3️⃣ SLA Breach Monitoring (Gauge + Pie)
st.markdown("### 📈 SLA Breach Monitoring")
if not filt.empty:
    sla_days = 2  # SLA threshold in days
    total_acts = len(filt)
    within_sla = (filt["Delay (Days)"] <= sla_days).sum()
    breached = total_acts - within_sla
    sla_compliance = round((within_sla / total_acts) * 100, 2) if total_acts > 0 else 0

    # Pie chart for SLA compliance
    sla_df = pd.DataFrame({
        "Status": ["Within SLA", "Breached"],
        "Count": [within_sla, breached]
    })

    pie = px.pie(
        sla_df, names="Status", values="Count",
        title=f"SLA Compliance (<= {sla_days} Days)",
        color="Status",
        color_discrete_map={"Within SLA": "green", "Breached": "red"}
    )
    st.plotly_chart(pie, use_container_width=True)

    st.metric("SLA Compliance %", f"{sla_compliance}%")
else:
    st.warning("No data available for SLA Monitoring.")



