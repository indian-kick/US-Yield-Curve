# === Imports ===
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from streamlit_plotly_events import plotly_events

# === Load Data ===
@st.cache_data
def load_data():
    df = pd.read_excel("US Yields.xlsx", header=None)
    df = df[df[1].apply(lambda x: isinstance(x, pd.Timestamp) or pd.to_datetime(x, errors='coerce') is not pd.NaT)]
    df.columns = ['Day', 'Date', '10Y', '2Y', '5Y', '30Y']
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['DateOnly'] = df['Date'].dt.date
    return df

# === Statistics Function ===
def compute_stats(series):
    return {
        'Mean': round(series.mean(), 3),
        'Std Dev': round(series.std(), 3),
        'Mean Abs Dev': round((series - series.mean()).abs().mean(), 3),
        'Min (Lower Bound)': round(series.min(), 3),
        'Max (Upper Bound)': round(series.max(), 3)
    }

# === Plot Function ===
def plot_with_bollinger(df, series, label):
    ma = series.rolling(window=20).mean()
    std = series.rolling(window=20).std()
    upper = ma + 2 * std
    lower = ma - 2 * std

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=series, mode='lines', name=label))
    fig.add_trace(go.Scatter(x=df['Date'], y=ma, mode='lines', name='MA(20)'))
    fig.add_trace(go.Scatter(x=df['Date'], y=upper, mode='lines', name='Upper Band', line=dict(width=0), showlegend=False))
    fig.add_trace(go.Scatter(x=df['Date'], y=lower, mode='lines', name='Lower Band', line=dict(width=0), fill='tonexty', fillcolor='rgba(255, 255, 0, 0.3)', showlegend=True))

    fig.update_layout(title=f"{label} with Bollinger Bands & MA", xaxis_title="Date", yaxis_title="Value",
                      xaxis=dict(tickformat='%Y-%m-%d'))
    return fig

# === Page Config ===
st.set_page_config(layout="wide")
st.title("Interactive US Treasury Yield Visualization")

# === Load & Filter Data ===
df = load_data()
maturities = ['2Y', '5Y', '10Y', '30Y']
min_date = df['Date'].min().date()
max_date = df['Date'].max().date()

st.sidebar.header("Select Time Frame for Plot")
start_date = st.sidebar.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

if start_date > end_date:
    st.sidebar.error("⚠️ Start date must be before or equal to end date.")
    st.stop()

df_filtered = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)].reset_index(drop=True)

# === Color Mapping ===
curve_colors = {
    '2Y': '#1f77b4',
    '5Y': '#ff7f0e',
    '10Y': '#2ca02c',
    '30Y': '#d62728'
}

# === Tabs ===
main_tab, outright_tab, spread_tab, fly_tab, condor_tab = st.tabs(["Yields & Curve", "Outrights", "Spreads", "Flies", "Condors"])

# === Yields & Curve Tab ===
with main_tab:
    st.subheader("Click a date on the yield time series or use arrow buttons")

    fig_ts_click = go.Figure()
    for col in maturities:
        fig_ts_click.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered[col], mode='lines', name=col, line=dict(color=curve_colors[col])))

    fig_ts_click.update_layout(title="Click on a date to show its yield curve", hovermode='x unified')
    selected = plotly_events(fig_ts_click, click_event=True)

    if 'date_index' not in st.session_state:
        st.session_state.date_index = len(df_filtered) - 1

    proposed_index = st.session_state.date_index
    
    col1, col2 = st.columns([1, 1])
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
    
    # Reset after handling
    st.session_state["prev_clicked"] = False
    st.session_state["next_clicked"] = False
    st.session_state.date_index = proposed_index

    row = df_filtered.iloc[proposed_index]
    yc = [row[m] for m in maturities]
    fig_yc = go.Figure()
    fig_yc.add_trace(go.Scatter(x=maturities, y=yc, mode='lines+markers', line=dict(color='black')))
    fig_yc.update_layout(title=f"Yield Curve on {row['DateOnly']}")
    st.plotly_chart(fig_yc, use_container_width=True)

    st.subheader("Yield Statistics")
    stat_start = st.date_input("Stats Start Date", min_date, min_value=min_date, max_value=max_date, key="main_stat_start")
    stat_end = st.date_input("Stats End Date", max_date, min_value=min_date, max_value=max_date, key="main_stat_end")
    stat_df = df[(df['Date'].dt.date >= stat_start) & (df['Date'].dt.date <= stat_end)]
    stats_df = pd.DataFrame([{**compute_stats(stat_df[m]), 'Maturity': m} for m in maturities])
    st.dataframe(stats_df.set_index('Maturity'))

# === Outright Tab ===
with outright_tab:
    st.subheader("Outright Yields")
    maturity = st.selectbox("Select Maturity", maturities, key="outright_select")
    fig = plot_with_bollinger(df_filtered, df_filtered[maturity], label=maturity)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Statistics")
    stat_start = st.date_input("Stats Start Date", min_date, min_value=min_date, max_value=max_date, key="out_stat_start")
    stat_end = st.date_input("Stats End Date", max_date, min_value=min_date, max_value=max_date, key="out_stat_end")
    stat_df = df[(df['Date'].dt.date >= stat_start) & (df['Date'].dt.date <= stat_end)]
    st.write(compute_stats(stat_df[maturity]))

# === Spread Tab ===
with spread_tab:
    st.subheader("Spreads (r2 - r1)")
    leg1 = st.selectbox("Leg 1", maturities, key="spread1")
    leg2 = st.selectbox("Leg 2", maturities, index=1, key="spread2")
    if leg1 != leg2:
        spread = df_filtered[leg2] - df_filtered[leg1]
        st.plotly_chart(plot_with_bollinger(df_filtered, spread, f"{leg2} - {leg1}"), use_container_width=True)

        st.subheader("Statistics")
        stat_start = st.date_input("Stats Start Date", min_date, min_value=min_date, max_value=max_date, key="spread_stat_start")
        stat_end = st.date_input("Stats End Date", max_date, min_value=min_date, max_value=max_date, key="spread_stat_end")
        stat_df = df[(df['Date'].dt.date >= stat_start) & (df['Date'].dt.date <= stat_end)]
        spread_stat = stat_df[leg2] - stat_df[leg1]
        st.write(compute_stats(spread_stat))
    else:
        st.warning("Please select different maturities")

# === Fly Tab ===
with fly_tab:
    st.subheader("Flies (2*r2 - r1 - r3)")
    r1 = st.selectbox("r1", maturities, key="fly1")
    r2 = st.selectbox("r2 (center)", maturities, index=1, key="fly2")
    r3 = st.selectbox("r3", maturities, index=2, key="fly3")
    if len({r1, r2, r3}) == 3:
        fly = 2 * df_filtered[r2] - df_filtered[r1] - df_filtered[r3]
        st.plotly_chart(plot_with_bollinger(df_filtered, fly, f"2*{r2} - {r1} - {r3}"), use_container_width=True)

        st.subheader("Statistics")
        stat_start = st.date_input("Stats Start Date", min_date, min_value=min_date, max_value=max_date, key="fly_stat_start")
        stat_end = st.date_input("Stats End Date", max_date, min_value=min_date, max_value=max_date, key="fly_stat_end")
        stat_df = df[(df['Date'].dt.date >= stat_start) & (df['Date'].dt.date <= stat_end)]
        fly_stat = 2 * stat_df[r2] - stat_df[r1] - stat_df[r3]
        st.write(compute_stats(fly_stat))
    else:
        st.warning("Select 3 different maturities")

# === Condor Tab ===
with condor_tab:
    st.subheader("Condors (r4 - 3*r3 + 3*r2 - r1)")
    r1 = st.selectbox("r1", maturities, key="d1")
    r2 = st.selectbox("r2", maturities, index=1, key="d2")
    r3 = st.selectbox("r3", maturities, index=2, key="d3")
    r4 = st.selectbox("r4", maturities, index=3, key="d4")
    if len({r1, r2, r3, r4}) == 4:
        condor = df_filtered[r4] - 3 * df_filtered[r3] + 3 * df_filtered[r2] - df_filtered[r1]
        st.plotly_chart(plot_with_bollinger(df_filtered, condor, f"{r4} - 3*{r3} + 3*{r2} - {r1}"), use_container_width=True)

        st.subheader("Statistics")
        stat_start = st.date_input("Stats Start Date", min_date, min_value=min_date, max_value=max_date, key="condor_stat_start")
        stat_end = st.date_input("Stats End Date", max_date, min_value=min_date, max_value=max_date, key="condor_stat_end")
        stat_df = df[(df['Date'].dt.date >= stat_start) & (df['Date'].dt.date <= stat_end)]
        condor_stat = stat_df[r4] - 3 * stat_df[r3] + 3 * stat_df[r2] - stat_df[r1]
        st.write(compute_stats(condor_stat))
    else:
        st.warning("Select 4 different maturities")
