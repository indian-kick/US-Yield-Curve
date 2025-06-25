import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import itertools
from streamlit_plotly_events import plotly_events

# === Load data ===
@st.cache_data
def load_data():
    df = pd.read_excel("US Yields.xlsx", header=None)
    df = df[df[1].apply(lambda x: isinstance(x, pd.Timestamp) or pd.to_datetime(x, errors='coerce') is not pd.NaT)]
    df.columns = ['Day', 'Date', '10Y', '2Y', '5Y', '30Y']
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['DateOnly'] = df['Date'].dt.date
    return df

# === Page config ===
st.set_page_config(layout="wide")
st.title("Interactive US Treasury Yield Visualization")

df = load_data()
maturities = ['2Y', '5Y', '10Y', '30Y']

# === Tabs ===
main_tab, spread_tab, fly_tab, defly_tab = st.tabs(["Yields & Curve", "Spreads", "Flies", "Deflies"])

# === Color mapping ===
curve_colors = {
    '2Y': '#1f77b4',
    '5Y': '#ff7f0e',
    '10Y': '#2ca02c',
    '30Y': '#d62728'
}

# === Initial state ===
if 'date_index' not in st.session_state:
    st.session_state.date_index = len(df) - 1

# === Main Tab: Yield Time Series and Curve ===
with main_tab:
    st.subheader("Click a date on the yield time series or use arrow buttons")

    # Plot Time Series with click support
    fig_ts_click = go.Figure()
    for col in maturities:
        fig_ts_click.add_trace(go.Scatter(
            x=df['Date'], y=df[col], mode='lines',
            name=col, line=dict(color=curve_colors[col])
        ))
    fig_ts_click.update_layout(
        title="Click on a date to show its yield curve",
        xaxis_title="Date", yaxis_title="Yield (%)",
        hovermode='x unified'
    )

    selected = plotly_events(fig_ts_click, click_event=True, hover_event=False)

    # Set index to current session value
    proposed_index = st.session_state.date_index

    # Handle button clicks
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("⬅️ Previous", key="prev_button"):
            proposed_index = max(0, proposed_index - 1)
            st.session_state["prev_clicked"] = True
            st.session_state["next_clicked"] = False
    with col2:
        if st.button("➡️ Next", key="next_button"):
            proposed_index = min(len(df) - 1, proposed_index + 1)
            st.session_state["next_clicked"] = True
            st.session_state["prev_clicked"] = False

    # Override only if no button was clicked
    if selected and not st.session_state.get("prev_clicked", False) and not st.session_state.get("next_clicked", False):
        proposed_index = selected[0]["pointIndex"]

    # Reset flags
    st.session_state["prev_clicked"] = False
    st.session_state["next_clicked"] = False

    # Save final index
    st.session_state.date_index = proposed_index

    # Show Yield Curve for selected date
    row = df.iloc[st.session_state.date_index]
    date_label = row['DateOnly']
    yc = [row[m] for m in maturities]

    fig_yc = go.Figure()
    fig_yc.add_trace(go.Scatter(
        x=maturities, y=yc, mode='lines+markers', line=dict(color='black')
    ))
    fig_yc.update_layout(
        title=f"Yield Curve on {date_label}",
        xaxis_title="Maturity", yaxis_title="Yield (%)"
    )

    st.plotly_chart(fig_yc, use_container_width=True)

with spread_tab:
    st.subheader("Spreads (r2 - r1)")
    c1, c2 = st.columns(2)
    with c1:
        leg1 = st.selectbox("Select Leg 1", ['2Y', '5Y', '10Y', '30Y'], key="spread_leg1")
    with c2:
        leg2 = st.selectbox("Select Leg 2", ['2Y', '5Y', '10Y', '30Y'], index=1, key="spread_leg2")

    if leg1 != leg2:
        spread = df[leg2] - df[leg1]
        fig_spread = go.Figure()
        fig_spread.add_trace(go.Scatter(x=df['Date'], y=spread, mode='lines', name=f"{leg2} - {leg1}"))
        fig_spread.update_layout(title=f"Spread: {leg2} - {leg1}", xaxis_title="Date", yaxis_title="Spread (%)",
                                 xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig_spread, use_container_width=True)
    else:
        st.warning("Please select two different maturities.")

with fly_tab:
    st.subheader("Flies (r1 + r3 - 2*r2)")
    fly1 = st.selectbox("Select r1", ['2Y', '5Y', '10Y', '30Y'], key="fly1")
    fly2 = st.selectbox("Select r2 (center)", ['2Y', '5Y', '10Y', '30Y'], index=1, key="fly2")
    fly3 = st.selectbox("Select r3", ['2Y', '5Y', '10Y', '30Y'], index=2, key="fly3")

    if len({fly1, fly2, fly3}) == 3:
        fly = df[fly1] + df[fly3] - 2 * df[fly2]
        fig_fly = go.Figure()
        fig_fly.add_trace(go.Scatter(x=df['Date'], y=fly, mode='lines', name=f"{fly1} + {fly3} - 2*{fly2}"))
        fig_fly.update_layout(title=f"Fly: {fly1} + {fly3} - 2*{fly2}", xaxis_title="Date", yaxis_title="Fly (%)",
                              xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig_fly, use_container_width=True)
    else:
        st.warning("Please select 3 different maturities.")

with defly_tab:
    st.subheader("Deflies (r4 - 3*r3 + 3*r2 - r1)")
    d1 = st.selectbox("Select r1", ['2Y', '5Y', '10Y', '30Y'], key="d1")
    d2 = st.selectbox("Select r2", ['2Y', '5Y', '10Y', '30Y'], index=1, key="d2")
    d3 = st.selectbox("Select r3", ['2Y', '5Y', '10Y', '30Y'], index=2, key="d3")
    d4 = st.selectbox("Select r4", ['2Y', '5Y', '10Y', '30Y'], index=3, key="d4")

    if len({d1, d2, d3, d4}) == 4:
        defly = df[d4] - 3 * df[d3] + 3 * df[d2] - df[d1]
        fig_defly = go.Figure()
        fig_defly.add_trace(go.Scatter(x=df['Date'], y=defly, mode='lines', name=f"Defly"))
        fig_defly.update_layout(title=f"Defly: {d4} - 3*{d3} + 3*{d2} - {d1}", xaxis_title="Date", yaxis_title="Defly (%)",
                                xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig_defly, use_container_width=True)
    else:
        st.warning("Please select 4 different maturities.")
