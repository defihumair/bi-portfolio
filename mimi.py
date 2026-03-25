import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Mimi Tracker 💙", layout="centered")

st.title("💙 Mimi Cycle Tracker")

# ---- SESSION STATE ----
if "base_dates_str" not in st.session_state:
    # Save the default string in session state so it persists
    st.session_state.base_dates_str = "2025-08-18, 2025-09-12, 2025-10-05, 2025-11-03, 2025-11-29, 2025-12-27, 2026-01-20, 2026-02-15, 2026-03-13"

# Grab the active dates from memory
dates_input = st.session_state.base_dates_str

# ---- CONVERT BASE DATES ----
try:
    base_dates = [datetime.strptime(d.strip(), "%Y-%m-%d") for d in dates_input.split(",")]
    base_dates = sorted(base_dates)
except:
    st.error("Invalid format in base dates")
    st.stop()

# ---- CALCULATE AVERAGE CYCLE ----
cycle_lengths = [(base_dates[i] - base_dates[i-1]).days for i in range(1, len(base_dates))]
avg_cycle = int(sum(cycle_lengths) / len(cycle_lengths)) if cycle_lengths else 26

# TODAY'S DATE
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

# ---- GENERATE FULL TIMELINE (Filling the gaps) ----
# We start from the last base date and keep adding 'avg_cycle' until we pass 'today'
full_timeline = base_dates.copy()
current_date = base_dates[-1]

# Keep adding periods until we reach into the future
while current_date < (today + timedelta(days=365)): 
    current_date = current_date + timedelta(days=avg_cycle)
    full_timeline.append(current_date)

# ---- SPLIT PAST & FUTURE ----
past_dates = [d for d in full_timeline if d <= today]
future_dates = [d for d in full_timeline if d > today]

# ---- TABS ----
tab1, tab2 = st.tabs(["📜 Past Data", "🔮 Future"])

# =====================
# 📜 PAST TAB (Linked to Base Data!)
# =====================
with tab1:
    st.subheader("Edit Past Periods")
    st.info(f"Average Cycle: **{avg_cycle} days**")
    
    # We will collect any changes you make in these boxes
    updated_past_dates = []

    # Displaying all dates found/generated up to today as editable boxes
    for i, d in enumerate(past_dates):
        # We add a label to show if it was a calculated guess or an exact fact
        label = "✅ Confirmed" if d in base_dates else "📅 Calculated"
        
        new_date = st.date_input(
            f"Period {i+1} ({label})",
            value=d,
            key=f"past_{i}"
        )
        updated_past_dates.append(new_date)

    # A button to save any changes you made in the boxes above back to the Base Data
    if st.button("💾 Update Base Data & Recalculate"):
        # Convert the dates from the boxes back into a comma-separated string
        new_base_string = ", ".join([d.strftime("%Y-%m-%d") for d in updated_past_dates])
        
        # Save it to the app's memory
        st.session_state.base_dates_str = new_base_string
        
        st.success("Dates saved! The Future predictions have been updated.")
        st.rerun() # This instantly refreshes the app with the new math

# =====================
# 🔮 FUTURE TAB
# =====================
with tab2:
    st.subheader("Future Predictions")
    months = st.selectbox("Select Range (months)", [3, 6, 12])
    limit_days = months * 30

    # Filter future dates based on selection
    future_filtered = [d for d in future_dates if (d - today).days <= limit_days]

    for d in future_filtered:
        st.write(f"📅 **Next Period Starts:** {d.strftime('%d %B %Y')}")

    st.divider()

    # ---- SAFE WINDOW ----
    st.subheader("🟢 Safest Days")
    st.caption("Note: The safest time is the 'Luteal Phase' (a few days after ovulation until the next period). Calendar methods are never 100% risk-free.")
    
    for d in future_filtered:
        # Ovulation is roughly 14 days before the next period
        ovulation_day = d - timedelta(days=14)
        
        # The fertile window ends about 2 days after ovulation.
        # So the "Safe Window" starts 3 days after ovulation and ends the day before her next period.
        safe_start = ovulation_day + timedelta(days=3)
        safe_end = d - timedelta(days=1)
        
        st.write(f"🛡️ **{safe_start.strftime('%d %b')} → {safe_end.strftime('%d %b')}**")

st.divider()
st.caption("Tracking active and updated securely.")