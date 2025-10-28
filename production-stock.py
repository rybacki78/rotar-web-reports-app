import streamlit as st
import pandas as pd
from pathlib import Path
import altair as alt
import os


st.set_page_config(
    page_title="Production stock analysis dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

st.logo("assets/Logo-Rotar-lichtgrijs.png", icon_image="assets/Logo-Rotar-lichtgrijs.png", size="medium")

"""
# :material/query_stats: Production stock analysis

Checking production stocks quantity and value in assortment groups.
"""

cols = st.columns([1, 3])

ASSORTMENTS = ["200004", "200003", "200002", "200001", "200000", "200100", "300000"]
DEFAULT_ASSORTMENTS = ["200000", "200100", "300000"]
CSV_PATH = "data/"
CSV_QUANTITY = os.path.join(CSV_PATH, "stock_quantity.csv")
CSV_VALUE = os.path.join(CSV_PATH, "stock_value.csv")


def assortments_to_str(assortments):
    return ",".join(assortments)


if "tickers_input" not in st.session_state:
    st.session_state.tickers_input = st.query_params.get(
        "assortments", assortments_to_str(DEFAULT_ASSORTMENTS)
    ).split(",")


def update_query_param():
    if st.session_state.tickers_input:
        st.query_params["assortments"] = assortments_to_str(
            st.session_state.tickers_input
        )
    else:
        st.query_params.pop("assortments", None)


top_left_cell = cols[0].container(
    border=True, height="content", vertical_alignment="top"
)

with top_left_cell:
    """
    ## Assortments information:

    * 200004 - pre-cut, grinded and bended parts
    * 200003 - welded parts
    * 200002 - parts in primer
    * 200001 - machined parts
    * 200000 - machined parts 2 (mostly sticks)
    * 200100 - assembled machines in primer
    * 300000 - finished goods (painted machines)
    """

    tickers = st.multiselect(
        "Assortments",
        options=(set(ASSORTMENTS) | set(st.session_state.tickers_input)),
        default=st.session_state.tickers_input,
        placeholder="Choose ASSORTMENTS. Example: 200000",
        accept_new_options=True,
    )

horizon_map = {
    "3 Months": "3",
    "6 Months": "6",
    "1 Year": "12",
    "3 Years": "36",
    "5 Years": "60",
    "10 Years": "600",
}

with top_left_cell:
    horizon = st.pills(
        "Time horizon",
        options=list(horizon_map.keys()),
        default="1 Year",
    )

if tickers:
    st.query_params["assortments"] = assortments_to_str(tickers)
else:
    st.query_params.pop("assortments", None)

if not horizon:
    top_left_cell.info("Pick some time period to compare", icon=":material/info:")
    st.stop()

if not tickers:
    top_left_cell.info("Pick some assortments to compare", icon=":material/info:")
    st.stop()


right_top_cell = cols[1].container(
    border=True, height="stretch", vertical_alignment="center"
)

right_bottom_cell = cols[1].container(
    border=True, height="stretch", vertical_alignment="center"
)


@st.cache_resource(ttl="2d", show_spinner=True)
def load_data():
    return pd.read_csv(CSV_VALUE, parse_dates=["date"]), pd.read_csv(
        CSV_QUANTITY, parse_dates=["date"]
    )


def narrow_data(tickers, period):
    df_value, df_quantity = load_data()
    needed_columns = ["date"] + tickers

    return df_value[needed_columns].tail(period), df_quantity[needed_columns].tail(
        period
    )


df_value, df_quantity = narrow_data(tickers, int(horizon_map[horizon]))

cols = [c for c in df_value.columns if c != "date"]
value_long = df_value.melt(
    id_vars="date", value_vars=cols, var_name="series", value_name="value"
)
tick_values = pd.date_range(
    df_value["date"].min().normalize(), df_value["date"].max().normalize(), freq="ME"
)

value_chart = (
    alt.Chart(value_long, title="Evolution of production stock values")
    .mark_line()
    .encode(
        x=alt.X(
            "date:T",
            axis=alt.Axis(
                title=None,
                values=list(tick_values),
                format="%b %y",
                tickSize=4,
            ),
        ),
        y=alt.Y(
            "value:Q",
            axis=alt.Axis(title="Value", format="~s"),
        ),
        color=alt.Color("series:N", title="Assortments"),
    )
    .properties(height=400)
    .interactive()
)

quantity_long = df_quantity.melt(
    id_vars="date", value_vars=cols, var_name="series", value_name="quantity"
)
tick_quantities = pd.date_range(
    df_quantity["date"].min().normalize(),
    df_quantity["date"].max().normalize(),
    freq="ME",
)

quantity_chart = (
    alt.Chart(quantity_long, title="Evolution of production stock quantities")
    .mark_line()
    .encode(
        x=alt.X(
            "date:T",
            axis=alt.Axis(
                title=None,
                values=list(tick_quantities),
                format="%b %y",
                tickSize=4,
            ),
        ),
        y=alt.Y(
            "quantity:Q",
            axis=alt.Axis(title="Quantity", format="~s"),
        ),
        color=alt.Color("series:N", title="Assortments"),
    )
    .properties(height=400)
    .interactive()
)

with right_top_cell:
    st.altair_chart(value_chart)

with right_bottom_cell:
    st.altair_chart(quantity_chart)


"""
Raw Data
"""

column_config = {
    "date": st.column_config.DateColumn("Month", format="MMM YYYY"),
    "200000": st.column_config.NumberColumn(format="localized"),
    "200001": st.column_config.NumberColumn(format="localized"),
    "200002": st.column_config.NumberColumn(format="localized"),
    "200003": st.column_config.NumberColumn(format="localized"),
    "200004": st.column_config.NumberColumn(format="localized"),
    "200100": st.column_config.NumberColumn(format="localized"),
    "300000": st.column_config.NumberColumn(format="localized"),
}


st.dataframe(df_value, hide_index=True, column_config=column_config)
st.dataframe(df_quantity, hide_index=True, column_config=column_config)
