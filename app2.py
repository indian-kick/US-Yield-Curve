import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import itertools

@st.cache_data
def load_data():
    df = pd.read_excel("US Yields.xlsx", header=None)
    df = df[df[1].apply(lambda x: isinstance(x, pd.Timestamp) or pd.to_datetime(x, errors='coerce') is not pd.NaT)]
    df.columns = ['Day', 'Date', '10Y', '2Y', '5Y', '30Y']
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['DateOnly'] = df['Date'].dt.date
    return df

st.set_page_config(layout="wide")
st.title("Interactive US Treasury Yield Visualization")

df = load_data()
maturities = ['2Y', '5Y', '10Y', '30Y']

# === Tabs ===
main_tab, spread_tab, fly_tab, defly_tab = st.tabs(["Yields & Curve", "Spreads", "Flies", "Deflies"])

from streamlit_plotly_events import plotly_events

# Set curve colors
curve_colors = {
    '2Y': '#1f77b4',
    '5Y': '#ff7f0e',
    '10Y': '#2ca02c',
    '30Y': '#d62728'
}

with main_tab:
    st.subheader("Click a date on the yield time series to view yield curve")

    # Initialize state on first run
    if 'date_index' not in st.session_state:
        st.session_state.date_index = len(df) - 1  # Default to latest date

    # Build time series chart
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

    # Capture click events
    selected = plotly_events(fig_ts_click, click_event=True, hover_event=False)
    if selected:
        st.session_state.date_index = selected[0]["pointIndex"]

    # Navigation buttons — store clicks in a temp variable
    prev_clicked = st.button("⬅️ Previous")
    next_clicked = st.button("➡️ Next")

    if prev_clicked:
        st.session_state.date_index = max(0, st.session_state.date_index - 1)
    if next_clicked:
        st.session_state.date_index = min(len(df) - 1, st.session_state.date_index + 1)

    # Extract selected row and plot yield curve
    clicked_row = df.iloc[st.session_state.date_index]
    clicked_date = clicked_row['DateOnly']
    yc = [clicked_row[m] for m in maturities]

    fig_yc = go.Figure()
    fig_yc.add_trace(go.Scatter(x=maturities, y=yc, mode='lines+markers', line=dict(color='black')))
    fig_yc.update_layout(
        title=f"Yield Curve on {clicked_date}",
        xaxis_title="Maturity", yaxis_title="Yield (%)"
    )
    st.plotly_chart(fig_yc, use_container_width=True)



# === All possible spreads ===
with spread_tab:
    st.subheader("All Spreads: (r2 - r1)")
    pairs = [(a, b) for i, a in enumerate(maturities) for b in maturities[i+1:]]
    for r1, r2 in pairs:
        spread = df[r2] - df[r1]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=spread, mode='lines', name=f"{r2} - {r1}"))
        fig.update_layout(title=f"Spread: {r2} - {r1}", xaxis_title="Date", yaxis_title="Spread (%)",
                          xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig, use_container_width=True)

# === All possible flies ===
with fly_tab:
    st.subheader("All Flies: (r1 + r3 - 2*r2)")
    fly_combos = [combo for combo in itertools.permutations(maturities, 3) if len(set(combo)) == 3]
    fly_combos = list(set(tuple(sorted(combo)) for combo in fly_combos))  # unique triplets
    for r1, r2, r3 in fly_combos:
        fly = df[r1] + df[r3] - 2 * df[r2]
        label = f"{r1} + {r3} - 2*{r2}"
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=fly, mode='lines', name=label))
        fig.update_layout(title=f"Fly: {label}", xaxis_title="Date", yaxis_title="Fly (%)",
                          xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig, use_container_width=True)

# === All possible deflies ===
with defly_tab:
    st.subheader("All Deflies: (r4 - 3*r3 + 3*r2 - r1)")
    defly_combos = [combo for combo in itertools.permutations(maturities, 4) if len(set(combo)) == 4]
    defly_combos = list(set(tuple(sorted(combo)) for combo in defly_combos))  # unique quartets
    for r1, r2, r3, r4 in defly_combos:
        defly = df[r4] - 3 * df[r3] + 3 * df[r2] - df[r1]
        label = f"{r4} - 3*{r3} + 3*{r2} - {r1}"
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=defly, mode='lines', name=label))
        fig.update_layout(title=f"Defly: {label}", xaxis_title="Date", yaxis_title="Defly (%)",
                          xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig, use_container_width=True)
