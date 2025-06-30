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

# === Date Range Selector (Separate Inputs) ===
st.sidebar.header("Select Time Frame")
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()

start_date = st.sidebar.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date, key="start_date")
end_date = st.sidebar.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date, key="end_date")

# Validation check
if start_date > end_date:
    st.sidebar.error("⚠️ Start date must be before or equal to end date.")
    st.stop()

# Apply filter
df_filtered = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)].reset_index(drop=True)

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
if 'date_index' not in st.session_state or st.session_state.date_index >= len(df_filtered):
    st.session_state.date_index = len(df_filtered) - 1

# === Main Tab: Yield Time Series and Curve ===
with main_tab:
    st.subheader("Click a date on the yield time series or use arrow buttons")

    fig_ts_click = go.Figure()
    for col in maturities:
        fig_ts_click.add_trace(go.Scatter(
            x=df_filtered['Date'], y=df_filtered[col], mode='lines',
            name=col, line=dict(color=curve_colors[col])
        ))
    fig_ts_click.update_layout(
        title="Click on a date to show its yield curve",
        xaxis_title="Date", yaxis_title="Yield (%)",
        hovermode='x unified'
    )

    selected = plotly_events(fig_ts_click, click_event=True, hover_event=False)

    proposed_index = st.session_state.date_index

    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("⬅️ Previous", key="prev_button"):
            proposed_index = max(0, proposed_index - 1)
            st.session_state["prev_clicked"] = True
            st.session_state["next_clicked"] = False
    with col2:
        if st.button("➡️ Next", key="next_button"):
            proposed_index = min(len(df_filtered) - 1, proposed_index + 1)
            st.session_state["next_clicked"] = True
            st.session_state["prev_clicked"] = False

    if selected and not st.session_state.get("prev_clicked", False) and not st.session_state.get("next_clicked", False):
        proposed_index = selected[0]["pointIndex"]

    st.session_state["prev_clicked"] = False
    st.session_state["next_clicked"] = False
    st.session_state.date_index = proposed_index

    # Yield Curve chart (initial or static view)
    maturity_map = {
        '2Y': 2,
        '5Y': 5,
        '10Y': 10,
        '30Y': 30
    }
    row = df_filtered.iloc[st.session_state.date_index]
    date_label = row['DateOnly']
    yc = [row[m] for m in maturities]
    
    # Map maturities to numeric values
    maturities_numeric = [maturity_map[m] for m in maturities]
    
    fig_yc = go.Figure()
    fig_yc.add_trace(go.Scatter(
        x=maturities_numeric, y=yc, mode='lines+markers', line=dict(color='black')
    ))
    fig_yc.update_layout(
        title=f"Yield Curve on {date_label}",
        xaxis_title="Maturity (Years)", yaxis_title="Yield (%)",
        xaxis=dict(
            tickmode='array',
            tickvals=maturities_numeric,
            ticktext=maturities  # This ensures labels are displayed as '2Y', '5Y', etc.
        )
    )
    
    st.plotly_chart(fig_yc, use_container_width=True)


    st.subheader("Yield Statistics (Selected Date Range)")

    stats_data = []
    for m in maturities:
        mean = df_filtered[m].mean()
        std = df_filtered[m].std()
        min_val = df_filtered[m].min()
        max_val = df_filtered[m].max()
        stats_data.append({
            'Maturity': m,
            'Mean': round(mean, 3),
            'Std Dev': round(std, 3),
            'Min (Lower Bound)': round(min_val, 3),
            'Max (Upper Bound)': round(max_val, 3)
        })

    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df.set_index('Maturity'))


   
# === Spread Tab ===
with spread_tab:
    st.subheader("Spreads (r2 - r1)")
    c1, c2 = st.columns(2)
    with c1:
        leg1 = st.selectbox("Select Leg 1", maturities, key="spread_leg1")
    with c2:
        leg2 = st.selectbox("Select Leg 2", maturities, index=1, key="spread_leg2")

    if leg1 != leg2:
        spread = df_filtered[leg2] - df_filtered[leg1]
        fig_spread = go.Figure()
        fig_spread.add_trace(go.Scatter(x=df_filtered['Date'], y=spread, mode='lines', name=f"{leg2} - {leg1}"))
        fig_spread.update_layout(title=f"Spread: {leg2} - {leg1}", xaxis_title="Date", yaxis_title="Spread (%)",
                                 xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig_spread, use_container_width=True)
        st.subheader("Spread Statistics")
        mean = spread.mean()
        std = spread.std()
        min_val = spread.min()
        max_val = spread.max()
        st.write(f"**Mean:** {round(mean, 3)}  \n"
                 f"**Std Dev:** {round(std, 3)}  \n"
                 f"**Min (Lower Bound):** {round(min_val, 3)}  \n"
                 f"**Max (Upper Bound):** {round(max_val, 3)}")

    else:
        st.warning("Please select two different maturities.")

# === Fly Tab ===
with fly_tab:
    st.subheader("Flies (r1 + r3 - 2*r2)")
    fly1 = st.selectbox("Select r1", maturities, key="fly1")
    fly2 = st.selectbox("Select r2 (center)", maturities, index=1, key="fly2")
    fly3 = st.selectbox("Select r3", maturities, index=2, key="fly3")

    if len({fly1, fly2, fly3}) == 3:
        fly = df_filtered[fly1] + df_filtered[fly3] - 2 * df_filtered[fly2]
        fig_fly = go.Figure()
        fig_fly.add_trace(go.Scatter(x=df_filtered['Date'], y=fly, mode='lines', name=f"{fly1} + {fly3} - 2*{fly2}"))
        fig_fly.update_layout(title=f"Fly: {fly1} + {fly3} - 2*{fly2}", xaxis_title="Date", yaxis_title="Fly (%)",
                              xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig_fly, use_container_width=True)
        st.subheader("Fly Statistics")
        mean = fly.mean()
        std = fly.std()
        min_val = fly.min()
        max_val = fly.max()
        st.write(f"**Mean:** {round(mean, 3)}  \n"
                 f"**Std Dev:** {round(std, 3)}  \n"
                 f"**Min (Lower Bound):** {round(min_val, 3)}  \n"
                 f"**Max (Upper Bound):** {round(max_val, 3)}")

    else:
        st.warning("Please select 3 different maturities.")

# === Defly Tab ===
with defly_tab:
    st.subheader("Deflies (r4 - 3*r3 + 3*r2 - r1)")
    d1 = st.selectbox("Select r1", maturities, key="d1")
    d2 = st.selectbox("Select r2", maturities, index=1, key="d2")
    d3 = st.selectbox("Select r3", maturities, index=2, key="d3")
    d4 = st.selectbox("Select r4", maturities, index=3, key="d4")

    if len({d1, d2, d3, d4}) == 4:
        defly = df_filtered[d4] - 3 * df_filtered[d3] + 3 * df_filtered[d2] - df_filtered[d1]
        fig_defly = go.Figure()
        fig_defly.add_trace(go.Scatter(x=df_filtered['Date'], y=defly, mode='lines', name=f"Defly"))
        fig_defly.update_layout(title=f"Defly: {d4} - 3*{d3} + 3*{d2} - {d1}", xaxis_title="Date", yaxis_title="Defly (%)",
                                xaxis=dict(tickformat='%Y-%m-%d'))
        st.plotly_chart(fig_defly, use_container_width=True)
        st.subheader("Defly Statistics")
        mean = defly.mean()
        std = defly.std()
        min_val = defly.min()
        max_val = defly.max()
        st.write(f"**Mean:** {round(mean, 3)}  \n"
                 f"**Std Dev:** {round(std, 3)}  \n"
                 f"**Min (Lower Bound):** {round(min_val, 3)}  \n"
                 f"**Max (Upper Bound):** {round(max_val, 3)}")

    else:
        st.warning("Please select 4 different maturities.")
