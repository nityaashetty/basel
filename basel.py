import streamlit as st
from scipy.stats import norm
import math

st.set_page_config(page_title="Basel III Capital Calculator", page_icon=None, layout="wide")

# ---------------------------------------------------------------------------
# Styling — black background, muted slate accents, no neon.
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
    div[data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #2a2d33; flex-wrap: wrap; }
    button[data-baseweb="tab"] { color: #8a8f98; font-weight: 500; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #eceef1; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("Basel III Capital Adequacy Calculator")
st.markdown('<div class="app-subtitle">Educational tool. Not for regulatory reporting or capital planning decisions.</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Shared helper for rendering a result card
# ---------------------------------------------------------------------------
def render_metric(label, value_str, requirement_html=""):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value_str}</div>
        {requirement_html}
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# IRB math (BCBS corporate/sovereign/bank risk-weight formula)
# ---------------------------------------------------------------------------
def irb_capital(pd, lgd, maturity):
    # PD must be strictly between 0 and 1 for the formula to be defined
    pd = min(max(pd, 0.0003), 0.9999)
    R = 0.12 * (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)) + \
        0.24 * (1 - (1 - math.exp(-50 * pd)) / (1 - math.exp(-50)))
    b = (0.11852 - 0.05478 * math.log(pd)) ** 2
    term = norm.cdf((1 - R) ** -0.5 * norm.ppf(pd) + (R / (1 - R)) ** 0.5 * norm.ppf(0.999))
    k_unadjusted = lgd * term - pd * lgd
    maturity_adj = (1 + (maturity - 2.5) * b) / (1 - 1.5 * b)
    k = k_unadjusted * maturity_adj
    return max(k, 0.0), R, b

tabs = st.tabs([
    "Expected Loss",
    "IRB Capital (K)",
    "RWA",
    "Capital Ratio",
    "Leverage Ratio",
    "Guide",
])
tab_el, tab_k, tab_rwa, tab_car, tab_lev, tab_guide = tabs

# ---------------------------------------------------------------------------
# TAB 1 — EXPECTED LOSS
# ---------------------------------------------------------------------------
with tab_el:
    st.subheader("Expected Loss (EL)")
    st.caption("EL = PD × LGD × EAD — the average loss a bank expects to take on an exposure.")

    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        pd_el = st.number_input("Probability of Default (PD, %)", min_value=0.01, max_value=100.0, value=1.0, step=0.01, key="pd_el")
        lgd_el = st.number_input("Loss Given Default (LGD, %)", min_value=0.0, max_value=100.0, value=45.0, step=1.0, key="lgd_el")
        ead_el = st.number_input("Exposure at Default (EAD, $)", min_value=0.0, value=1000000.0, step=10000.0, format="%.2f", key="ead_el")
        calc_el = st.button("Calculate Expected Loss", type="primary", use_container_width=True)
    with c2:
        if calc_el:
            el = (pd_el / 100) * (lgd_el / 100) * ead_el
            el_pct = (pd_el / 100) * (lgd_el / 100) * 100
            render_metric("Expected Loss", f"${el:,.2f}")
            render_metric("Expected Loss as % of EAD", f"{el_pct:.4f}%")
            st.session_state["ead_shared"] = ead_el
        else:
            st.info("Enter PD, LGD, and EAD, then click Calculate.")

# ---------------------------------------------------------------------------
# TAB 2 — IRB CAPITAL (K)
# ---------------------------------------------------------------------------
with tab_k:
    st.subheader("IRB Capital Requirement (K)")
    st.caption("Basel IRB formula for corporate/sovereign/bank exposures. K is the capital "
               "requirement as a fraction of EAD, covering unexpected losses.")

    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        pd_k = st.number_input("Probability of Default (PD, %)", min_value=0.01, max_value=100.0, value=1.0, step=0.01, key="pd_k")
        lgd_k = st.number_input("Loss Given Default (LGD, %)", min_value=0.0, max_value=100.0, value=45.0, step=1.0, key="lgd_k")
        ead_k = st.number_input("Exposure at Default (EAD, $)", min_value=0.0, value=1000000.0, step=10000.0, format="%.2f", key="ead_k")
        maturity_k = st.number_input("Effective Maturity (years)", min_value=1.0, max_value=5.0, value=2.5, step=0.1, key="maturity_k")
        calc_k = st.button("Calculate IRB Capital", type="primary", use_container_width=True)
    with c2:
        if calc_k:
            k, R, b = irb_capital(pd_k / 100, lgd_k / 100, maturity_k)
            capital_dollar = k * ead_k
            render_metric("Capital Requirement (K)", f"{k*100:.4f}%")
            render_metric("Capital Requirement ($)", f"${capital_dollar:,.2f}")
            render_metric("Asset Correlation (R)", f"{R*100:.4f}%")
            render_metric("Maturity Adjustment (b)", f"{b:.6f}")
            st.session_state["k_shared"] = k
            st.session_state["ead_shared"] = ead_k
        else:
            st.info("Enter PD, LGD, EAD, and Maturity, then click Calculate.")

# ---------------------------------------------------------------------------
# TAB 3 — RWA
# ---------------------------------------------------------------------------
with tab_rwa:
    st.subheader("Risk-Weighted Assets (RWA)")
    st.caption("Credit RWA = K × 12.5 × EAD. Total RWA = Credit RWA + Market RWA + Operational RWA.")

    st.markdown("**Credit RWA (from IRB Capital)**")
    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        default_k = st.session_state.get("k_shared", 0.08)
        default_ead = st.session_state.get("ead_shared", 1000000.0)
        k_rwa = st.number_input("Capital Requirement K (%)", min_value=0.0, max_value=100.0,
                                 value=float(default_k * 100), step=0.01, key="k_rwa",
                                 help="Carried over from the IRB Capital tab if calculated there.")
        ead_rwa = st.number_input("Exposure at Default (EAD, $)", min_value=0.0,
                                   value=float(default_ead), step=10000.0, format="%.2f", key="ead_rwa")
        calc_credit_rwa = st.button("Calculate Credit RWA", type="primary", use_container_width=True)
    with c2:
        credit_rwa_val = None
        if calc_credit_rwa:
            credit_rwa_val = (k_rwa / 100) * 12.5 * ead_rwa
            render_metric("Credit RWA", f"${credit_rwa_val:,.2f}")
            st.session_state["credit_rwa_shared"] = credit_rwa_val
        else:
            st.info("Enter K and EAD, then click Calculate.")

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("**Total RWA (Credit + Market + Operational)**")
    c3, c4 = st.columns([1, 1], gap="large")
    with c3:
        credit_default = st.session_state.get("credit_rwa_shared", 0.0)
        credit_total = st.number_input("Credit Risk RWA ($)", min_value=0.0, value=float(credit_default), step=10000.0, format="%.2f", key="credit_total")
        market_total = st.number_input("Market Risk RWA ($)", min_value=0.0, value=0.0, step=10000.0, format="%.2f", key="market_total")
        op_total = st.number_input("Operational Risk RWA ($)", min_value=0.0, value=0.0, step=10000.0, format="%.2f", key="op_total")
        calc_total_rwa = st.button("Calculate Total RWA", type="primary", use_container_width=True)
    with c4:
        if calc_total_rwa:
            total_rwa_val = credit_total + market_total + op_total
            render_metric("Total RWA", f"${total_rwa_val:,.2f}")
            st.session_state["total_rwa_shared"] = total_rwa_val
        else:
            st.info("Enter Credit, Market, and Operational RWA, then click Calculate.")

# ---------------------------------------------------------------------------
# TAB 4 — CAPITAL RATIO
# ---------------------------------------------------------------------------
with tab_car:
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
        default_total_rwa = st.session_state.get("total_rwa_shared", 0.0)
        credit_rwa = st.number_input("Credit Risk RWA — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
        market_rwa = st.number_input("Market Risk RWA — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
        op_rwa = st.number_input("Operational Risk RWA — $", min_value=0.0, value=0.0, step=1000.0, format="%.2f")
        if default_total_rwa > 0:
            st.caption(f"Total RWA calculated on the RWA tab: ${default_total_rwa:,.2f}. "
                       "You can split it across the three fields above, or enter figures directly.")

        st.subheader("Capital Buffers (%)")
        ccb = st.number_input("Capital Conservation Buffer (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1)
        ccyb = st.number_input("Countercyclical Buffer (%)", min_value=0.0, max_value=2.5, value=0.0, step=0.1)
        srb = st.number_input("Systemic Risk Buffer (%)", min_value=0.0, max_value=5.0, value=0.0, step=0.1)

        calculate = st.button("Calculate Capital Ratios", type="primary", use_container_width=True)

    with col_result:
        st.subheader("Results")

        if not calculate:
            st.info("Enter your capital details and click Calculate Capital Ratios to see results.")
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

                min_cet1 = 4.5
                min_tier1 = 6.0
                min_total = 8.0

                buffer_total = ccb + ccyb + srb

                req_cet1 = min_cet1 + buffer_total
                req_tier1 = min_tier1 + buffer_total
                req_total = min_total + buffer_total

                def render_ratio(label, value, requirement):
                    passed = value >= requirement
                    status_class = "status-pass" if passed else "status-fail"
                    status_text = "MEETS REQUIREMENT" if passed else "BELOW REQUIREMENT"
                    render_metric(label, f"{value:.2f}%",
                                  f'<div class="{status_class}">{status_text} (req. {requirement:.2f}%)</div>')

                render_ratio("CET1 Ratio", cet1_ratio, req_cet1)
                render_ratio("Tier 1 Ratio", tier1_ratio, req_tier1)
                render_ratio("Total Capital Adequacy Ratio (CAR)", car, req_total)

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
# TAB 5 — LEVERAGE RATIO
# ---------------------------------------------------------------------------
with tab_lev:
    st.subheader("Leverage Ratio")
    st.caption("Leverage Ratio = Tier 1 Capital / Total Exposure. A non-risk-based backstop, "
               "minimum 3% under Basel III.")

    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        tier1_lev = st.number_input("Tier 1 Capital ($)", min_value=0.0, value=0.0, step=10000.0, format="%.2f", key="tier1_lev")
        exposure_lev = st.number_input("Total Exposure ($)", min_value=0.0, value=0.0, step=10000.0, format="%.2f", key="exposure_lev",
                                        help="On-balance-sheet exposures + derivatives + securities financing + off-balance-sheet items.")
        calc_lev = st.button("Calculate Leverage Ratio", type="primary", use_container_width=True)
    with c2:
        if calc_lev:
            if exposure_lev <= 0:
                st.error("Total Exposure must be greater than zero.")
            else:
                lev_ratio = tier1_lev / exposure_lev * 100
                min_lev = 3.0
                passed = lev_ratio >= min_lev
                status_class = "status-pass" if passed else "status-fail"
                status_text = "MEETS REQUIREMENT" if passed else "BELOW REQUIREMENT"
                render_metric("Leverage Ratio", f"{lev_ratio:.2f}%",
                              f'<div class="{status_class}">{status_text} (req. {min_lev:.1f}%)</div>')
        else:
            st.info("Enter Tier 1 Capital and Total Exposure, then click Calculate.")

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

    ### RWA Build-Up Hierarchy

    Total RWA is not a single number — it is built bottom-up through a chain of calculations.
    For credit exposures under the Internal Ratings-Based (IRB) approach, the chain looks like this:

    ```
    PD, LGD, EAD, Maturity
            |
            v
    Basel IRB Formula  ->  K (capital requirement, % of EAD)
            |
            v
    Credit RWA = K x 12.5 x EAD
            |
            v
    Total RWA = Credit RWA + Market RWA + Operational RWA
    ```

    Market RWA and Operational RWA are calculated under separate Basel frameworks (standardized
    or internal models) and are not derived from PD/LGD/EAD — only Credit RWA is, under IRB.
    This calculator treats Market and Operational RWA as direct inputs for that reason.

    ### Expected Loss (EL)
    **EL = PD × LGD × EAD**

    This is the loss a bank expects on average and is meant to be covered by pricing and
    provisions, not by regulatory capital. Regulatory capital instead covers *unexpected* loss —
    the gap between expected loss and a high-confidence worst case.

    ### IRB Capital Requirement (K)
    The Basel IRB formula for corporate, sovereign, and bank exposures computes K, the capital
    requirement as a fraction of EAD, covering unexpected loss at a 99.9% confidence level:

    - **Asset correlation (R):** models how correlated a borrower's defaults are with the wider
      economy. Lower-PD (higher-quality) borrowers get a higher correlation weight.
    - **Maturity adjustment (b):** longer-maturity exposures carry more risk, so K scales up with
      effective maturity.
    - **K** combines these with the inverse cumulative normal distribution to estimate the loss
      threshold at a 99.9% confidence level, less the expected loss already covered by
      provisioning.

    This calculator implements the full BCBS corporate/sovereign/bank IRB formula (not the
    simplified retail version).

    ### From K to Credit RWA
    **Credit RWA = K × 12.5 × EAD**

    The 12.5 multiplier converts the capital requirement into a risk-weighted asset equivalent
    (12.5 = 1 / 8%, since the Basel minimum Total Capital ratio is 8%).

    ### Capital Tiers
    - **Common Equity Tier 1 (CET1):** the highest-quality capital — common shares, retained
      earnings, disclosed reserves.
    - **Additional Tier 1 (AT1):** perpetual instruments absorbing losses on a going-concern basis.
    - **Tier 1 Capital = CET1 + AT1**
    - **Tier 2 Capital:** subordinated debt and certain loan-loss reserves, absorbing losses on a
      gone-concern basis.
    - **Total Capital = Tier 1 + Tier 2**

    ### Core Capital Ratios
    | Ratio | Formula | Minimum |
    |---|---|---|
    | CET1 Ratio | CET1 / RWA | 4.5% |
    | Tier 1 Ratio | (CET1 + AT1) / RWA | 6.0% |
    | Total CAR | (Tier 1 + Tier 2) / RWA | 8.0% |
    | Leverage Ratio | Tier 1 Capital / Total Exposure | 3.0% |

    The Leverage Ratio is a non-risk-based backstop — it ignores RWA entirely and compares
    capital directly to total exposure, to catch cases where risk-weighting understates true risk.

    ### Capital Buffers (stacked on top of minimums)
    - **Capital Conservation Buffer (CCB):** fixed at 2.5% under the Basel III standard. Breaching
      it restricts discretionary distributions (dividends, buybacks, bonuses).
    - **Countercyclical Buffer (CCyB):** 0–2.5%, set by national regulators depending on credit
      growth conditions.
    - **Systemic Risk Buffer (SRB):** applied to systemically important banks (G-SIBs/D-SIBs);
      varies by jurisdiction and can exceed 2.5% for the largest institutions.

    A bank's effective required ratio = base minimum + CCB + CCyB + SRB.

    ### Worked Example — End to End
    - PD = 1.0%, LGD = 45%, EAD = \\$1,000,000, Maturity = 2.5 years
    - EL = 0.01 × 0.45 × 1,000,000 = **\\$4,500**
    - K (from IRB formula) ≈ **8–9%** depending on correlation and maturity adjustment
    - Credit RWA = K × 12.5 × EAD ≈ **\\$1,000,000–\\$1,125,000**
    - Add Market RWA + Operational RWA → Total RWA
    - CET1 = \\$8,000,000, AT1 = \\$2,000,000, Tier 2 = \\$3,000,000, Total RWA = \\$100,000,000
      → CET1 Ratio 8.0%, Tier 1 Ratio 10.0%, CAR 13.0% — all pass at 2.5% CCB.

    ### Limitations of this tool
    This calculator uses the standardized Basel III minimums and the BCBS corporate IRB formula.
    It does not account for jurisdiction-specific add-ons (e.g., Pillar 2 requirements, liquidity
    coverage ratio, NSFR), retail-specific IRB formulas, SME size adjustments, transitional
    arrangements, or Basel IV output floor adjustments. It is for learning purposes only.
    """)