import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd
# -----------------------
# Helper functions
# -----------------------

def irr(cashflows):
    try:
        return npf.irr(cashflows)
    except:
        return None

def amortization_schedule(loan_amount, rate, amort_years, term_years):
    """Returns interest, principal, and balance each year."""
    r = rate
    n = amort_years
payment = npf.pmt(r, n, -loan_amount)

    schedule = []
    balance = loan_amount

    for _ in range(term_years):
        interest = balance * r
        principal = payment - interest
        balance -= principal
        schedule.append({
            "payment": payment,
            "interest": interest,
            "principal": principal,
            "balance": max(balance, 0)
        })

    return schedule


# -----------------------
# Streamlit App
# -----------------------

st.title("🏢 CRE 10-Year Return Model")
st.caption("Simplified version of your Excel model focusing on the adjustable KPIs")

st.sidebar.header("Acquisition Inputs")

purchase_price = st.sidebar.number_input("Purchase Price", value=10_000_000)
noi_year_1 = st.sidebar.number_input("Year 1 NOI", value=750_000)
rent_growth = st.sidebar.slider("Revenue Growth (%)", 0.0, 5.0, 2.0) / 100
expense_growth = st.sidebar.slider("Expense Growth (%)", 0.0, 5.0, 2.0) / 100
exit_cap = st.sidebar.slider("Exit Cap Rate (%)", 4.0, 9.0, 6.0) / 100

st.sidebar.header("Debt Inputs")

ltv = st.sidebar.slider("LTV (%)", 0.0, 0.9, 0.6)
interest_rate = st.sidebar.slider("Interest Rate (%)", 2.0, 10.0, 6.0) / 100
amort_years = st.sidebar.selectbox("Amortization (Years)", [20, 25, 30], index=2)
loan_term = 10  # fixed 10 years

loan_amount = purchase_price * ltv
equity = purchase_price - loan_amount

st.subheader("📌 Acquisition Summary")
st.write(f"**Loan Amount:** ${loan_amount:,.0f}")
st.write(f"**Equity Required:** ${equity:,.0f}")

# -----------------------
# Year-by-year cash flow
# -----------------------

schedule = amortization_schedule(loan_amount, interest_rate, amort_years, loan_term)

noi_list = []
cf_list = []
dscr_list = []

noi = noi_year_1

for year in range(1, 11):
    debt_service = schedule[year-1]["payment"]

    # NOI growth
    if year > 1:
        noi = noi * (1 + rent_growth)

    cashflow = noi - debt_service

    noi_list.append(noi)
    cf_list.append(cashflow)
    dscr_list.append(noi / debt_service)

# -----------------------
# Exit value and sale proceeds
# -----------------------

exit_value = noi_list[-1] / exit_cap
remaining_balance = schedule[-1]["balance"]
net_sales_proceeds = exit_value - remaining_balance

# -----------------------
# Returns
# -----------------------

cashflows = [-equity] + cf_list[:-1] + [cf_list[-1] + net_sales_proceeds]
irr_val = irr(cashflows)
equity_multiple = sum(cashflows[1:]) / (-cashflows[0])

# -----------------------
# Output
# -----------------------

st.header("📊 10-Year Return Summary")

col1, col2, col3 = st.columns(3)
col1.metric("IRR", f"{irr_val*100:,.2f}%" if irr_val else "N/A")
col2.metric("Equity Multiple", f"{equity_multiple:,.2f}x")
col3.metric("Exit Value", f"${exit_value:,.0f}")

st.subheader("Cash Flow to Equity")
df = pd.DataFrame({
    "Year": list(range(1, 11)),
    "NOI": noi_list,
    "Debt Service": [s["payment"] for s in schedule],
    "Cash Flow": cf_list,
    "DSCR": dscr_list
})
st.dataframe(df.style.format({
    "NOI": "${:,.0f}",
    "Debt Service": "${:,.0f}",
    "Cash Flow": "${:,.0f}",
    "DSCR": "{:,.2f}"
}))

st.subheader("Cash Flow Chart")
st.line_chart(df.set_index("Year")["Cash Flow"])

st.subheader("NOI Growth Chart")
st.line_chart(df.set_index("Year")["NOI"])

st.subheader("DSCR Over Time")
st.line_chart(df.set_index("Year")["DSCR"])

st.success("App ready. Adjust inputs in the sidebar to see updated 10-year returns.")
