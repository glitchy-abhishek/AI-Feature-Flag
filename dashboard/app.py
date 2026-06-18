import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://localhost:8000"

st.set_page_config(page_title="AI Feature Flags", layout="wide")
st.title("🚦 AI Feature Flag & Quality Monitor")

# --- FETCH DATA ---
@st.cache_data(ttl=2) 
def fetch_data():
    try:
        flags = requests.get(f"{API_URL}/flags/").json()
        evals = requests.get(f"{API_URL}/evaluations/").json()
        return flags, evals
    except:
        return [], []

flags, evals = fetch_data()

if not flags:
    st.warning("No flags found or API is down.")
    st.stop()

# --- TOP METRICS (Using .get() for safety) ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Flags", len(flags))
active_flags = [f for f in flags if f.get("rollout_percentage", 0) > 0 and not f.get("rollback_triggered", False)]
col2.metric("Active Rollouts", len(active_flags))
rolled_back = [f for f in flags if f.get("rollback_triggered", False)]
col3.metric("Auto-Rolled Back", len(rolled_back))

st.markdown("---")

# --- FLAG CONTROLS & STATUS ---
st.subheader("Active Feature Flags")

# Clean up data before passing to pandas to prevent KeyErrors
clean_flags = []
for f in flags:
    clean_flags.append({
        "name": f.get("name", "Unknown"),
        "rollout_percentage": f.get("rollout_percentage", 0),
        "minimum_quality_score": f.get("minimum_quality_score", 3.0),
        "rollback_triggered": f.get("rollback_triggered", False)
    })

flag_df = pd.DataFrame(clean_flags)
st.dataframe(flag_df, use_container_width=True)

st.markdown("---")

# --- QUALITY MONITORING CHART ---
st.subheader("📈 Real-Time Quality Monitoring")

if evals:
    df_evals = pd.DataFrame(evals)
    # Safely filter
    if "variant_served" in df_evals.columns and "quality_score" in df_evals.columns:
        exp_evals = df_evals[(df_evals["variant_served"] == "experimental") & (df_evals["quality_score"] > 0)]
        
        if not exp_evals.empty:
            fig = px.line(
                exp_evals, 
                x=exp_evals.index, 
                y="quality_score", 
                color="flag_name",
                title="Experimental Variant Quality Scores",
                markers=True
            )
            fig.add_hline(y=3.5, line_dash="dot", annotation_text="Rollback Threshold", annotation_position="bottom right", line_color="red")
            fig.update_layout(yaxis_range=[0, 5.5], xaxis_title="Evaluation Number", yaxis_title="LLM Judge Score (1-5)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No graded experimental evaluations yet.")
    else:
        st.info("Awaiting evaluation data formats.")
else:
    st.info("No evaluation data available.")