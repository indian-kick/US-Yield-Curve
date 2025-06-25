import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# === Load and clean Excel data ===
@st.cache_data
def load_data():
    df = pd.read_excel("US Yields.xlsx", header=None)
    df = df[df[1].apply(lambda x: isinstance(x, pd.Timestamp) or pd.to_datetime(x, errors='coerce') is not pd.NaT)]
    df.columns = ['Day', 'Date', '10Y', '2Y', '5Y', '30Y']
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['DateOnly'] = df['Date'].dt.date
    return df

# === Streamlit layout ===
st.set_page_config(layout="wide")
st.title("Interactive US Treasury Yield Visualization")

df = load_data()

# Create tabs
main_tab, spread_tab, fly_tab, defly_tab = st.tabs(["Yields & Curve", "Spreads", "Flies", "Deflies"])

with main_tab:
    # === Time Series Plot ===
    fig_ts = go.Figure()
    for col in ['2Y', '5Y', '10Y', '30Y']:
        fig_ts.add_trace(go.Scatter(
            x=df['Date'], y=df[col], mode='lines', name=col
        ))

    fig_ts.update_layout(
        title="Treasury Yields Over Time",
        xaxis_title="Date",
        yaxis_title="Yield (%)",
        hovermode='x unified',
    )

    st.plotly_chart(fig_ts, use_container_width=True)

    clicked_point = st.plotly_events(fig_ts, click_event=True, override_height=600)

    if clicked_point:
        point_index = clicked_point[0]['pointIndex']
        clicked_date = df.iloc[point_index]['DateOnly']
        selected_row = df[df['DateOnly'] == clicked_date].iloc[0]
        maturities = ['2Y', '5Y', '10Y', '30Y']
        yields = [selected_row[m] for m in maturities]

        fig_yc = go.Figure()
        fig_yc.add_trace(go.Scatter(
            x=maturities, y=yields, mode='lines+markers', name=str(clicked_date)
        ))

        fig_yc.update_layout(
            title=f"Yield Curve on {clicked_date}",
            xaxis_title="Maturity",
            yaxis_title="Yield (%)"
        )

        st.plotly_chart(fig_yc, use_container_width=True)
    else:
        st.info("Click on a point in the yield time plot to view the yield curve below.")

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
        fig_spread.update_layout(title=f"Spread: {leg2} - {leg1}", xaxis_title="Date", yaxis_title="Spread (%)")
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
        fig_fly.update_layout(title=f"Fly: {fly1} + {fly3} - 2*{fly2}", xaxis_title="Date", yaxis_title="Fly (%)")
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
        fig_defly.update_layout(title=f"Defly: {d4} - 3*{d3} + 3*{d2} - {d1}", xaxis_title="Date", yaxis_title="Defly (%)")
        st.plotly_chart(fig_defly, use_container_width=True)
    else:
        st.warning("Please select 4 different maturities.")
