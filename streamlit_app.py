import streamlit as st

production_stock = st.Page("production-stock.py", title="📈 Production Stock")
stock_positions = st.Page("stock-positions.py", title="🏪 Stock Positions")
accounts_receivable = st.Page("accounts-receivable.py", title="📒 Accounts Receivable")


page=st.navigation([production_stock, stock_positions, accounts_receivable])
st.set_page_config (
    layout="wide",
)
page.run()
