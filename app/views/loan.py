"""Loan offer simulation."""

import streamlit as st

from app.views._helpers import require_case
from src.scoring.loan_simulator import simulate_loan


def page_loan_offer():
    st.title("Loan Offer")
    st.caption("Indicative limit and pricing based on health score and GST turnover.")

    if not require_case():
        return

    score = st.session_state.score_result["final_score"]
    turnover = st.session_state.features["gst_avg_monthly_turnover"]
    amount = st.slider("Requested amount (₹ Lakhs)", 5, 50, 15)

    result = simulate_loan(score, amount, turnover)

    if result["eligible"]:
        st.success(f"**Indicative approval: ₹{result['approved_lakhs']}L**")
    else:
        st.error(result["reason"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Grade", result["grade"])
    c2.metric("Max eligible", f"₹{result.get('max_eligible_lakhs', 0)}L")
    c3.metric("Rate", f"{result.get('interest_rate_pct', '—')}%")
    c4.metric("Tenure", f"{result.get('tenure_months', '—')} mo")
