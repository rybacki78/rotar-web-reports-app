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

st.logo(
    "assets/Logo-Rotar-lichtgrijs.png",
    icon_image="assets/Logo-Rotar-lichtgrijs.png",
    size="medium",
)

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
    "10 Years": "120",
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
    return pd.read_csv(CSV_VALUE, parse_dates=["date"], index_col="date"), pd.read_csv(
        CSV_QUANTITY, parse_dates=["date"], index_col="date"
    )


def narrow_data(tickers, period):
    df_value, df_quantity = load_data()

    print(df_value.info())

    # needed_columns = ["date"] + tickers

    return df_value[tickers].tail(period), df_quantity[tickers].tail(period)


df_value, df_quantity = narrow_data(tickers, int(horizon_map[horizon]))


def chart(df: pd.DataFrame):
    source = df.reset_index().melt("date", var_name="assortment", value_name="value")

    nearest = alt.selection_point(
        nearest=True, on="pointerover", fields=["date"], empty=False
    )

    line = (
        alt.Chart(source)
        .mark_line()
        .encode(
            alt.X(
                "yearmonth(date):T",
            ),
            alt.Y("value:Q", axis=alt.Axis(format="~s")),
            color="assortment:N",
        )
    )

    selectors = (
        alt.Chart(source)
        .mark_point()
        .encode(
            alt.X("yearmonth(date):T"),
            opacity=alt.value(0),
        )
        .add_params(nearest)
    )
    when_near = alt.when(nearest)

    points = line.mark_point().encode(
        opacity=when_near.then(alt.value(1)).otherwise(alt.value(0))
    )

    text = line.mark_text(align="left", dx=10, dy=-10, fontSize=14, fontWeight="bold").encode(
        text=when_near.then(alt.Text("value:Q", format=".2s")).otherwise(alt.value(" ")), color=alt.value("lightgray")
    )

    rules = (
        alt.Chart(source)
        .mark_rule(color="gray")
        .encode(
            alt.X("yearmonth(date):T"),
        )
        .transform_filter(nearest)
    )

    layers = alt.layer(line, selectors, points, rules, text).properties(height=400)

    return layers


with right_top_cell:
    st.altair_chart(chart(df_value))

with right_bottom_cell:
    st.altair_chart(chart(df_quantity))


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


st.dataframe(df_value, column_config=column_config)
st.dataframe(df_quantity, column_config=column_config)
