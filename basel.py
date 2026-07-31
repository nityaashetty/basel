import streamlit as st

st.set_page_config(page_title="Basel III Capital Calculator", page_icon=None, layout="wide")

# ---------------------------------------------------------------------------
# Styling — muted navy/slate, restrained accent, no bright or neon colors.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e4e6eb; }
    h1, h2, h3, h4 {
        color: #d8dbe3;
        font-family: 'Georgia', 'Times New Roman', serif;
        font-weight: 600;
    }
    p, span, label, div { font-family: 'Helvetica Neue', Arial, sans-serif; }
    .app-subtitle { color: #8a8f98; font-size: 0.95rem; margin-top: -8px; margin-bottom: 8px; }
    .metric-card {
        background-color: #121212;
        border: 1px solid #2a2d33;
        border-left: 3px solid #8892a6;
        border-radius: 4px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .metric-label {
        color: #8a8f98;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }
    .metric-value { font-size: 1.7rem; font-weight: 700; color: #eceef1; margin-top: 4px; }
    .status-pass { color: #4f9d73; font-weight: 600; font-size: 0.85rem; margin-top: 4px; }
    .status-fail { color: #c15a5a; font-weight: 600; font-size: 0.85rem; margin-top: 4px; }
    .section-divider { border-top: 1px solid #2a2d33; margin: 22px 0; }
    div[data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #2a2d33; }
    button[data-baseweb="tab"] { color: #8a8f98; font-weight: 500; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #eceef1; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("Basel III Capital Adequacy Calculator")
st.markdown('<div class="app-subtitle">Educational tool. Not for regulatory reporting or capital planning decisions.</div>', unsafe_allow_html=True)

tab_calc, tab_guide = st.tabs(["Calculator", "Guide"])

# ---------------------------------------------------------------------------
# CALCULATOR TAB
# ---------------------------------------------------------------------------
with tab_calc:
    col_input, col_result = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("Tier 1 Capital")
        cet1 = st.number_input("Common Equity Tier 1 (CET1) — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
        at1 = st.number_input("Additional Tier 1 (AT1) — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

        st.subheader("Tier 2 Capital")
        tier2 = st.number_input("Tier 2 Capital — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f",
                                 help="Required to compute Total Capital / CAR. Includes subordinated debt, "
                                      "loan-loss reserves, etc.")

        st.subheader("Risk-Weighted Assets (RWA)")
        credit_rwa = st.number_input("Credit Risk RWA — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
        market_rwa = st.number_input("Market Risk RWA — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
        op_rwa = st.number_input("Operational Risk RWA — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

        st.subheader("Capital Buffers (%)")
        ccb = st.number_input("Capital Conservation Buffer (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
        ccyb = st.number_input("Countercyclical Buffer (%)", min_value=0.0, max_value=2.5, value=0.0, step=0.1)
        srb = st.number_input("Systemic Risk Buffer (%)", min_value=0.0, max_value=5.0, value=0.0, step=0.1)

        calculate = st.button("Calculate Capital Ratios", type="primary", use_container_width=True)

    with col_result:
        st.subheader("Results")

        if not calculate:
            st.info("Enter your capital details and click **Calculate Capital Ratios** to see results.")
        else:
            total_rwa = credit_rwa + market_rwa + op_rwa

            if total_rwa <= 0:
                st.error("Total Risk-Weighted Assets must be greater than zero.")
            else:
                tier1_capital = cet1 + at1
                total_capital = tier1_capital + tier2

                cet1_ratio = cet1 / total_rwa * 100
                tier1_ratio = tier1_capital / total_rwa * 100
                car = total_capital / total_rwa * 100

                # Regulatory minimums (Basel III standard, pre-buffer)
                min_cet1 = 4.5
                min_tier1 = 6.0
                min_total = 8.0

                buffer_total = ccb + ccyb + srb

                req_cet1 = min_cet1 + buffer_total
                req_tier1 = min_tier1 + buffer_total
                req_total = min_total + buffer_total

                def render_metric(label, value, requirement=None):
                    status_html = ""
                    if requirement is not None:
                        passed = value >= requirement
                        status_class = "status-pass" if passed else "status-fail"
                        status_text = "MEETS REQUIREMENT" if passed else "BELOW REQUIREMENT"
                        status_html = f'<div class="{status_class}">{status_text} (req. {requirement:.2f}%)</div>'
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-label">{label}</div>
                        <div class="metric-value">{value:.2f}%</div>
                        {status_html}
                    </div>
                    """, unsafe_allow_html=True)

                render_metric("CET1 Ratio", cet1_ratio, req_cet1)
                render_metric("Tier 1 Ratio", tier1_ratio, req_tier1)
                render_metric("Total Capital Adequacy Ratio (CAR)", car, req_total)

                st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)
                c1.metric("Tier 1 Capital", f"${tier1_capital:,.0f}")
                c2.metric("Total Capital", f"${total_capital:,.0f}")
                c3.metric("Total RWA", f"${total_rwa:,.0f}")

                st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                st.markdown(f"""
                **Required minimum + buffers breakdown**
                - Base CET1 minimum: {min_cet1:.1f}% → with buffers: **{req_cet1:.2f}%**
                - Base Tier 1 minimum: {min_tier1:.1f}% → with buffers: **{req_tier1:.2f}%**
                - Base Total Capital minimum: {min_total:.1f}% → with buffers: **{req_total:.2f}%**
                - Combined buffer applied: {buffer_total:.2f}% (Conservation {ccb:.1f}% + Countercyclical {ccyb:.1f}% + Systemic Risk {srb:.1f}%)
                """)

                if all([cet1_ratio >= req_cet1, tier1_ratio >= req_tier1, car >= req_total]):
                    st.success("Bank is compliant with all Basel III minimum capital + buffer requirements.")
                else:
                    st.error("Bank does NOT meet one or more Basel III minimum capital + buffer requirements.")

# ---------------------------------------------------------------------------
# GUIDE TAB
# ---------------------------------------------------------------------------
with tab_guide:
    st.header("Basel III Capital Framework — Guide")

    st.markdown("""
    ### What is Basel III?
    Basel III is a global regulatory framework developed by the Basel Committee on Banking
    Supervision (BCBS) in response to the 2008 financial crisis. It strengthens bank capital
    requirements, introduces leverage and liquidity requirements, and aims to improve the
    banking sector's ability to absorb shocks.

    ### Capital Tiers
    - **Common Equity Tier 1 (CET1):** The highest-quality capital — common shares, retained
      earnings, and disclosed reserves. This is the primary loss-absorbing buffer for a bank.
    - **Additional Tier 1 (AT1):** Instruments such as perpetual bonds that absorb losses on a
      going-concern basis but rank below CET1.
    - **Tier 1 Capital = CET1 + AT1**
    - **Tier 2 Capital:** Supplementary capital — subordinated debt, certain loan-loss reserves —
      that absorbs losses on a gone-concern basis (i.e., in liquidation).
    - **Total Capital = Tier 1 + Tier 2**

    ### Risk-Weighted Assets (RWA)
    RWA scales a bank's assets by their riskiness. It is composed of three pillars:
    - **Credit Risk RWA** — risk of borrower default across loans and exposures.
    - **Market Risk RWA** — risk from trading book positions (interest rate, FX, equity, commodity).
    - **Operational Risk RWA** — risk from internal failures, fraud, systems, or external events.

    ### Core Ratios
    | Ratio | Formula | Minimum |
    |---|---|---|
    | CET1 Ratio | CET1 / RWA | 4.5% |
    | Tier 1 Ratio | (CET1 + AT1) / RWA | 6.0% |
    | Total CAR | (Tier 1 + Tier 2) / RWA | 8.0% |

    ### Capital Buffers (stacked on top of minimums)
    - **Capital Conservation Buffer (CCB):** Fixed at 2.5% under the Basel III standard. Breaching
      it restricts discretionary distributions (dividends, buybacks, bonuses).
    - **Countercyclical Buffer (CCyB):** 0–2.5%, set by national regulators depending on credit
      growth conditions — built up in good times, released in downturns.
    - **Systemic Risk Buffer (SRB):** Applied to systemically important banks (G-SIBs/D-SIBs);
      varies by jurisdiction and can exceed 2.5% for the largest institutions.

    A bank's **effective required ratio** = base minimum + CCB + CCyB + SRB.

    ### Worked Example
    - CET1 = \\$8,000,000, AT1 = \\$2,000,000, Tier 2 = \\$3,000,000
    - Credit RWA = \\$60,000,000, Market RWA = \\$15,000,000, Operational RWA = \\$25,000,000
    - Total RWA = \\$100,000,000
    - CET1 Ratio = 8,000,000 / 100,000,000 = **8.0%**
    - Tier 1 Ratio = 10,000,000 / 100,000,000 = **10.0%**
    - CAR = 13,000,000 / 100,000,000 = **13.0%**
    - With CCB 2.5%, CCyB 0%, SRB 0%: required CET1 = 7.0%, Tier 1 = 8.5%, Total = 10.5%
      → all three ratios pass.

    ### Limitations of this tool
    This calculator uses the standardized Basel III minimums and does not account for
    jurisdiction-specific add-ons (e.g., Pillar 2 requirements, leverage ratio, liquidity
    coverage ratio, NSFR), transitional arrangements, or Basel IV output floor adjustments.
    It is for learning purposes only.
    """)
