import streamlit as st

stock = st.Page("production-stock.py", title="📈 Production Stock")
report2 = st.Page("temp-placeholder.py", title="Report2")


page=st.navigation([stock, report2])
st.set_page_config (
    layout="wide",
)
page.run()
