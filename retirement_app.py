"""
Retirement Forecasting Streamlit App
A comprehensive tool for modeling retirement wealth across multiple scenarios.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
from datetime import datetime
from retirement_calculator import RetirementCalculator, Person
from tax_calculator import TaxCalculator
from scenario_manager import ScenarioManager
from report_generator import RetirementReportGenerator

# Page configuration
st.set_page_config(
    page_title="Retirement Wealth Forecaster",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern, professional CSS styling
st.markdown("""
    <style>
    /* Main layout */
    .main {
        padding: 0rem 2rem;
    }

    /* Clean headers without emojis */
    h1 {
        color: #1e3a8a;
        font-weight: 600;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }

    h2 {
        color: #374151;
        font-weight: 600;
        font-size: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }

    h3 {
        color: #4b5563;
        font-weight: 500;
        font-size: 1.1rem;
        margin-top: 1rem;
        margin-bottom: 0.75rem;
    }

    /* Modern metric cards */
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.25rem;
        border-radius: 0.75rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .stMetric label {
        color: white !important;
        font-weight: 500;
    }

    .stMetric [data-testid="stMetricValue"] {
        color: white !important;
        font-size: 1.5rem;
        font-weight: 600;
    }

    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #f9fafb;
        padding-top: 2rem;
    }

    /* Clean tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 2px solid #e5e7eb;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: #6b7280;
        border-radius: 0;
    }

    .stTabs [aria-selected="true"] {
        color: #1e3a8a;
        border-bottom: 3px solid #1e3a8a;
    }

    /* Input sections */
    .stExpander {
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: white;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 0.5rem;
        font-weight: 500;
        border: none;
        padding: 0.5rem 1.5rem;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    /* Clean dividers */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 1px solid #e5e7eb;
    }

    /* Info boxes */
    .info-box {
        background-color: #eff6ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }

    /* Success/Warning messages */
    .stSuccess {
        background-color: #f0fdf4;
        border-left: 4px solid #22c55e;
    }

    .stWarning {
        background-color: #fef3c7;
        border-left: 4px solid #f59e0b;
    }

    /* Better spacing for inputs */
    .stNumberInput, .stTextInput, .stSelectbox, .stSlider {
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)


def format_currency(value):
    """Format value as currency."""
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def format_percentage(value):
    """Format value as percentage."""
    return f"{value*100:.2f}%"


def main():
    """Main application function."""

    # Clean title without emojis
    st.title("Retirement Wealth Forecaster")
    st.markdown(
        "Plan your financial future with comprehensive modeling of income, expenses, taxes, and investments.")

    # Minimal sidebar for scenario management only
    with st.sidebar:
        st.header("Scenario Management")
        st.markdown("---")

        # Load scenario
        uploaded_file = st.file_uploader(
            "Load Scenario",
            type=["json"],
            help="Upload a previously saved scenario JSON file"
        )

        if uploaded_file is not None:
            try:
                scenario_data = json.load(uploaded_file)
                st.session_state['loaded_scenario'] = scenario_data
                st.success(
                    f"Loaded: {scenario_data.get('scenario_name', 'Unnamed')}")

                # Show scenario summary
                with st.expander("Scenario Details"):
                    st.text(
                        ScenarioManager.get_scenario_summary(scenario_data))

                # Button to apply loaded scenario
                col_apply, col_clear = st.columns(2)
                with col_apply:
                    if st.button(
                        "Apply",
                        type="primary",
                            use_container_width=True):
                        st.session_state['apply_scenario'] = True
                        # Set account types checkbox if scenario has account data
                        if scenario_data.get('financial', {}).get('account_balances') is not None:
                            st.session_state['account_types_checkbox'] = True
                        st.rerun()
                with col_clear:
                    if st.button("Clear", use_container_width=True):
                        st.session_state['loaded_scenario'] = None
                        st.session_state['apply_scenario'] = False
                        st.session_state['account_types_checkbox'] = False
                        st.rerun()
            except Exception as e:
                st.error(f"Error loading scenario: {str(e)}")
        elif st.session_state.get('loaded_scenario'):
            # Show loaded scenario status even without file upload
            st.info(
                f"Using: {st.session_state['loaded_scenario'].get('scenario_name', 'Unnamed')}")
            if st.button("Clear Loaded Scenario", use_container_width=True):
                st.session_state['loaded_scenario'] = None
                st.session_state['apply_scenario'] = False
                st.session_state['account_types_checkbox'] = False
                st.rerun()

        # Save scenario section
        st.markdown("**Save Current Scenario**")

        scenario_name = st.text_input(
            "Scenario Name",
            value=st.session_state.get('scenario_name', 'My Retirement Plan'),
            key="scenario_name_input",
            help="Name for your scenario (used in filename)"
        )

        save_clicked = st.button(
            "Save Scenario",
            use_container_width=True,
            help="Save current configuration as JSON")

        # Handle save scenario in sidebar
        if save_clicked:
            if st.session_state.get('current_params'):
                params = st.session_state['current_params']

                # Store the scenario name in session state
                st.session_state['scenario_name'] = scenario_name

                scenario = ScenarioManager.save_scenario(
                    scenario_name=scenario_name,
                    people=params['people'],
                    initial_assets=params['initial_assets'],
                    annual_expenses=params['annual_expenses'],
                    expense_growth_rate=params['expense_growth'],
                    investment_return_rate=params['investment_return'],
                    state=params['state'],
                    additional_contributions=params['additional_contributions'],
                    social_security_age=params['ss_age'],
                    social_security_benefit=params['ss_benefit'],
                    inflation_rate=params['inflation_rate'],
                    forecast_years=params['forecast_years'],
                    account_balances=params.get('account_balances'),
                    contribution_allocation=params.get('contribution_allocation'))

                json_str = ScenarioManager.scenario_to_json(scenario)

                st.download_button(
                    label="Download Scenario",
                    data=json_str,
                    file_name=f"{scenario_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="download_scenario_button")
                st.success(f"Scenario '{scenario_name}' ready for download!")
            else:
                st.warning("Please calculate a forecast first before saving.")
        
        st.markdown("---")
        
        # About section in sidebar
        with st.expander("About This Tool"):
            st.markdown("""
            ### How It Works
            
            This retirement forecasting tool models your financial future by considering:
            
            - **Income:** Salary/wages with growth, retirement income, and Social Security
            - **Expenses:** Living costs with inflation adjustment
            - **Investments:** Assets with compound growth and withdrawals
            - **Taxes:** Federal income tax, state tax, FICA, and capital gains tax
            
            ### Key Assumptions
            
            - Tax brackets and rates are based on 2024 IRS guidelines
            - Capital gains are realized proportionally when withdrawing from assets
            - FICA taxes (Social Security and Medicare) only apply to earned income
            - Investment returns are assumed constant (actual returns will vary)
            - Inflation affects both expenses and the "real" value of assets
            - **RSU Vesting**: Annual RSU vesting is treated as ordinary income
            - **RSUs Stop at Retirement**: When you retire, RSU vesting ends (unvested shares forfeited)
            
            ### Best Practices
            
            1. **Be Conservative:** Use realistic return rates (7% is historical stock market average)
            2. **Include Buffer:** Add 10-20% to expense estimates for unexpected costs
            3. **Test Scenarios:** Try different retirement ages and savings rates
            4. **Update Regularly:** Revisit your forecast annually as circumstances change
            
            ### Limitations
            
            This is a simplified model and doesn't account for:
            - Market volatility and sequence of returns risk
            - Healthcare costs (include in expenses)
            - Estate planning and inheritance
            - Tax law changes
            - Roth vs Traditional IRA distinctions
            
            **Disclaimer:** This tool is for educational purposes only and should not be considered financial advice.
            Consult with a qualified financial advisor for personalized recommendations.
            """)

    # Main content area with tabs
    # Check if we should apply a loaded scenario
    loaded_scenario = st.session_state.get('loaded_scenario')
    apply_scenario = st.session_state.get('apply_scenario', False)

    # Create tabs for Configure and Results
    tab_config, tab_results = st.tabs(["Configure", "Results"])

    with tab_config:
        st.markdown("### Scenario Configuration")
        st.markdown("Configure your retirement scenario parameters below.")
        st.markdown("---")

        # Household Configuration
        st.subheader("Household")

        # Pre-populate from loaded scenario if available
        if loaded_scenario:
            default_num_adults = len(loaded_scenario['people'])
        else:
            default_num_adults = 1

        num_adults = st.number_input(
            "Number of Adults",
            min_value=1,
            max_value=4,
            value=default_num_adults,
            step=1,
            key="num_adults")

        people = []
        for i in range(num_adults):
            # Get defaults from loaded scenario if available
            if loaded_scenario and i < len(loaded_scenario['people']):
                person_data = loaded_scenario['people'][i]
                default_name = person_data['name']
                default_age = person_data['age']
                default_ret_age = person_data['retirement_age']
                default_income = person_data['current_income']
                default_rsu = person_data.get('annual_rsu_vesting', 0)
                default_growth = person_data['income_growth_rate']
                default_ret_income = person_data['retirement_income']
            else:
                default_name = f"Person {i+1}"
                default_age = 30
                default_ret_age = 65
                default_income = 75000
                default_rsu = 0
                default_growth = 0.03
                default_ret_income = 0

            with st.expander(f"Person {i+1} Details", expanded=(i == 0)):
                name = st.text_input(
                    f"Name", value=default_name, key=f"name_{i}")
                age = st.number_input(
                    f"Current Age",
                    min_value=18,
                    max_value=100,
                    value=default_age,
                    step=1,
                    key=f"age_{i}")
                retirement_age = st.number_input(
                    f"Retirement Age",
                    min_value=age,
                    max_value=100,
                    value=max(default_ret_age, age),
                    step=1,
                    key=f"ret_age_{i}"
                )
                current_income = st.number_input(
                    f"Annual Cash Salary",
                    min_value=0,
                    max_value=10000000,
                    value=int(default_income),
                    step=5000,
                    key=f"income_{i}",
                    help="Base salary/wages (not including RSUs)"
                )

                # RSU Income Section
                annual_rsu_vesting = st.number_input(
                    f"Annual RSU Vesting Income",
                    min_value=0,
                    max_value=5000000,
                    value=int(default_rsu),
                    step=5000,
                    key=f"rsu_vesting_{i}",
                    help="Annual amount of RSUs that vest (taxed as income, stops at retirement)"
                )

                income_growth = st.number_input(
                    f"Annual Income Growth Rate",
                    min_value=0.0,
                    max_value=0.20,
                    value=float(default_growth),
                    step=0.01,
                    format="%.2f",
                    key=f"growth_{i}",
                    help="Annual growth in salary and RSU vesting (raises, promotions)"
                )

                retirement_income = st.number_input(
                    f"Annual Income in Retirement (e.g., pension)",
                    min_value=0,
                    max_value=1000000,
                    value=int(default_ret_income),
                    step=5000,
                    key=f"ret_income_{i}"
                )

                # Show total compensation
                total_comp = current_income + annual_rsu_vesting
                if annual_rsu_vesting > 0:
                    st.info(
                        f"Total Compensation: ${total_comp:,.0f} (${current_income:,.0f} cash + ${annual_rsu_vesting:,.0f} RSU vesting)")

                person = Person(
                    name=name,
                    age=age,
                    retirement_age=retirement_age,
                    current_income=current_income,
                    income_growth_rate=income_growth,
                    retirement_income=retirement_income,
                    annual_rsu_vesting=annual_rsu_vesting
                )
                people.append(person)

        # Financial Configuration
        st.subheader("Financial Assets & Expenses")

        # Pre-populate financial settings from loaded scenario
        if loaded_scenario:
            fin_defaults = loaded_scenario['financial']
            default_assets = fin_defaults['initial_assets']
            default_expenses = fin_defaults['annual_expenses']
            default_contributions = fin_defaults['additional_contributions']
            default_expense_growth = fin_defaults['expense_growth_rate']
        else:
            default_assets = 100000
            default_expenses = 60000
            default_contributions = 20000
            default_expense_growth = 0.03

        initial_assets = st.number_input(
            "Current Investment Assets",
            min_value=0,
            max_value=100000000,
            value=int(default_assets),
            step=10000,
            help="Total value of investment accounts (401k, IRA, brokerage, etc.)")

        # Account Type Breakdown (Advanced)
        # Check if loaded scenario has account balances
        has_account_data = (loaded_scenario and 
                           loaded_scenario.get('financial', {}).get('account_balances') is not None)
        
        use_account_types = st.checkbox(
            "Specify Account Types (Advanced)",
            key="account_types_checkbox",
            help="Break down assets by Traditional, Roth, Taxable for tax-optimized withdrawals"
        )

        account_balances = None
        contribution_allocation = None

        if use_account_types:
            # Get default values from loaded scenario if available
            if has_account_data:
                saved_balances = loaded_scenario['financial']['account_balances']
                default_trad_401k = int(saved_balances.get('traditional_401k', 0))
                default_trad_ira = int(saved_balances.get('traditional_ira', 0))
                default_roth_401k = int(saved_balances.get('roth_401k', 0))
                default_roth_ira = int(saved_balances.get('roth_ira', 0))
                default_taxable = int(saved_balances.get('taxable', 0))
                default_hsa = int(saved_balances.get('hsa', 0))
            else:
                default_trad_401k = 0
                default_trad_ira = 0
                default_roth_401k = 0
                default_roth_ira = 0
                default_taxable = 0
                default_hsa = 0
            
            st.markdown("**Account Balances:**")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("*Tax-Deferred:*")
                traditional_401k = st.number_input(
                    "Traditional 401k",
                    min_value=0,
                    max_value=10000000,
                    value=default_trad_401k,
                    step=10000,
                    key="traditional_401k"
                )
                traditional_ira = st.number_input(
                    "Traditional IRA",
                    min_value=0,
                    max_value=10000000,
                    value=default_trad_ira,
                    step=10000,
                    key="traditional_ira"
                )

                st.markdown("*Tax-Free:*")
                roth_401k = st.number_input(
                    "Roth 401k",
                    min_value=0,
                    max_value=10000000,
                    value=default_roth_401k,
                    step=10000,
                    key="roth_401k"
                )

            with col2:
                roth_ira = st.number_input(
                    "Roth IRA",
                    min_value=0,
                    max_value=10000000,
                    value=default_roth_ira,
                    step=10000,
                    key="roth_ira"
                )

                st.markdown("*Taxable:*")
                taxable = st.number_input(
                    "Taxable Brokerage",
                    min_value=0,
                    max_value=100000000,
                    value=default_taxable,
                    step=10000,
                    key="taxable"
                )
                hsa = st.number_input(
                    "HSA",
                    min_value=0,
                    max_value=500000,
                    value=default_hsa,
                    step=1000,
                    key="hsa"
                )

            account_balances = {
                'traditional_401k': traditional_401k,
                'traditional_ira': traditional_ira,
                'roth_401k': roth_401k,
                'roth_ira': roth_ira,
                'taxable': taxable,
                'hsa': hsa
            }

            total_accounts = sum(account_balances.values())
            if total_accounts != initial_assets and total_accounts > 0:
                st.warning(
                    f"Account total (${total_accounts:,.0f}) doesn't match initial assets (${initial_assets:,.0f})")
            elif total_accounts > 0:
                st.success(f"Total: ${total_accounts:,.0f}")

        annual_expenses = st.number_input(
            "Annual Living Expenses",
            min_value=0,
            max_value=10000000,
            value=int(default_expenses),
            step=5000,
            help="Total annual spending (housing, food, transportation, etc.)"
        )

        additional_contributions = st.number_input(
            "Annual Additional Savings",
            min_value=0,
            max_value=1000000,
            value=int(default_contributions),
            step=5000,
            help="Additional amount to save each year while working"
        )

        # Contribution Allocation (if using account types)
        if use_account_types and additional_contributions > 0:
            st.markdown("**Where do new savings go?**")
            
            # Get default values from loaded scenario if available
            if has_account_data and loaded_scenario['financial'].get('contribution_allocation'):
                saved_allocation = loaded_scenario['financial']['contribution_allocation']
                default_contrib_trad = int(saved_allocation.get('traditional_401k', 0.6) * 100)
                default_contrib_roth = int(saved_allocation.get('roth_ira', 0.3) * 100)
                default_contrib_taxable = int(saved_allocation.get('taxable', 0.1) * 100)
            else:
                default_contrib_trad = 60
                default_contrib_roth = 30
                default_contrib_taxable = 10

            contrib_traditional = st.slider(
                "% to Traditional 401k/IRA",
                min_value=0,
                max_value=100,
                value=default_contrib_trad,
                step=5,
                help="Tax-deferred growth, taxed at withdrawal"
            )
            contrib_roth = st.slider(
                "% to Roth IRA",
                min_value=0,
                max_value=100,
                value=default_contrib_roth,
                step=5,
                help="Tax-free growth and withdrawals"
            )
            contrib_taxable = st.slider(
                "% to Taxable",
                min_value=0,
                max_value=100,
                value=default_contrib_taxable,
                step=5,
                help="Most flexible, capital gains tax on growth"
            )

            total_pct = contrib_traditional + contrib_roth + contrib_taxable
            if total_pct != 100:
                st.error(
                    f"Allocation must sum to 100% (currently {total_pct}%)")
                contribution_allocation = None
            else:
                contribution_allocation = {
                    'traditional_401k': contrib_traditional / 100,
                    'roth_ira': contrib_roth / 100,
                    'taxable': contrib_taxable / 100
                }
                st.info(
                    f"Allocation: {contrib_traditional}% Traditional, {contrib_roth}% Roth, {contrib_taxable}% Taxable")

        # Investment Configuration
        st.subheader("Investment Assumptions")

        # Pre-populate investment settings from loaded scenario
        if loaded_scenario:
            inv_defaults = loaded_scenario['investment']
            default_return = inv_defaults['investment_return_rate']
            default_inflation = inv_defaults['inflation_rate']
        else:
            default_return = 0.07
            default_inflation = 0.025

        investment_return = st.slider(
            "Expected Annual Return",
            min_value=0.0,
            max_value=0.15,
            value=float(default_return),
            step=0.01,
            format="%.2f",
            help="Expected annual return on investments"
        )

        expense_growth = st.slider(
            "Expense Growth Rate",
            min_value=0.0,
            max_value=0.10,
            value=float(default_expense_growth),
            step=0.01,
            format="%.2f",
            help="Expected annual increase in expenses"
        )

        inflation_rate = st.slider(
            "Inflation Rate",
            min_value=0.0,
            max_value=0.10,
            value=float(default_inflation),
            step=0.005,
            format="%.3f",
            help="Expected annual inflation rate"
        )

        # Tax Configuration
        st.subheader("Tax Configuration")

        # Pre-populate state from loaded scenario
        if loaded_scenario:
            default_state = loaded_scenario['taxes']['state']
            state_list = list(TaxCalculator.STATE_TAX_RATES.keys())
            default_state_index = state_list.index(
                default_state) if default_state in state_list else 0
        else:
            default_state_index = 0

        state = st.selectbox(
            "State of Residence",
            options=list(TaxCalculator.STATE_TAX_RATES.keys()),
            index=default_state_index,
            help="Select your state for tax calculations"
        )

        # Social Security
        st.subheader("Social Security")

        # Pre-populate SS from loaded scenario
        if loaded_scenario:
            default_ss_age = loaded_scenario['social_security']['age']
            default_ss_benefit = loaded_scenario['social_security']['benefit']
            default_include_ss = default_ss_benefit > 0
        else:
            default_ss_age = 67
            default_ss_benefit = 30000
            default_include_ss = False

        include_ss = st.checkbox(
            "Include Social Security Benefits",
            value=default_include_ss)

        if include_ss:
            ss_age = st.number_input(
                "Social Security Starting Age",
                min_value=62,
                max_value=70,
                value=default_ss_age,
                step=1
            )
            ss_benefit = st.number_input(
                "Annual Social Security Benefit (Total Household)",
                min_value=0,
                max_value=200000,
                value=int(default_ss_benefit),
                step=1000,
                help="Estimated annual Social Security benefits"
            )
        else:
            ss_age = 67
            ss_benefit = 0

        # Forecast Period
        st.subheader("Forecast Period")

        # Pre-populate forecast years from loaded scenario
        if loaded_scenario:
            default_forecast_years = loaded_scenario['forecast']['years']
        else:
            default_forecast_years = 50

        forecast_years = st.slider(
            "Years to Forecast",
            min_value=10,
            max_value=70,
            value=default_forecast_years,
            step=5
        )

        st.markdown("---")

        # Summary metrics before calculation
        st.markdown("### Current Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Current Income",
                format_currency(sum(p.current_income for p in people))
            )

        with col2:
            st.metric(
                "Annual Expenses",
                format_currency(annual_expenses)
            )

        with col3:
            st.metric(
                "Starting Assets",
                format_currency(initial_assets)
            )

        # Calculate forecast button
        calculate_clicked = st.button(
            "Calculate Forecast",
            type="primary",
            use_container_width=True)

        if calculate_clicked:
            with st.spinner("Calculating your retirement forecast..."):
                calculator = RetirementCalculator(
                    people=people,
                    initial_assets=initial_assets,
                    annual_expenses=annual_expenses,
                    expense_growth_rate=expense_growth,
                    investment_return_rate=investment_return,
                    state=state,
                    additional_contributions=additional_contributions,
                    social_security_age=ss_age,
                    social_security_benefit=ss_benefit,
                    inflation_rate=inflation_rate,
                    account_balances=account_balances,
                    contribution_allocation=contribution_allocation
                )

                forecast_df = calculator.calculate_forecast(
                    years=forecast_years)
                summary = calculator.calculate_summary_metrics(forecast_df)

                # Store in session state
                st.session_state['forecast_df'] = forecast_df
                st.session_state['summary'] = summary
                st.session_state['current_params'] = {
                    'people': people,
                    'initial_assets': initial_assets,
                    'annual_expenses': annual_expenses,
                    'expense_growth': expense_growth,
                    'investment_return': investment_return,
                    'state': state,
                    'additional_contributions': additional_contributions,
                    'ss_age': ss_age,
                    'ss_benefit': ss_benefit,
                    'inflation_rate': inflation_rate,
                    'forecast_years': forecast_years,
                    'account_balances': account_balances,
                    'contribution_allocation': contribution_allocation
                }
                st.success(
                    "Forecast calculated! View results in the 'Results' tab.")

    # Results Tab
    with tab_results:
        if 'forecast_df' not in st.session_state or 'summary' not in st.session_state:
            st.info("No forecast results yet. Configure your scenario in the 'Configure' tab and click 'Calculate Forecast'.")
        elif 'forecast_df' in st.session_state and 'summary' in st.session_state:
            forecast_df = st.session_state['forecast_df']
            summary = st.session_state['summary']

            st.markdown("### Forecast Results")
            st.markdown("Review your retirement projection below.")

            # Summary metrics
            st.subheader("Key Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if summary.get('retirement_assets'):
                    st.metric(
                        "Assets at Retirement",
                        format_currency(summary['retirement_assets']),
                        help="Total assets when first person retires"
                    )

            with col2:
                st.metric(
                    "Peak Assets",
                    format_currency(summary['peak_assets']),
                    f"Year {int(summary['peak_year'])}"
                )

            with col3:
                st.metric(
                    "Final Assets",
                    format_currency(summary['final_assets']),
                    f"Age {int(summary['final_age'])}"
                )

            with col4:
                st.metric(
                    "Total Taxes Paid",
                    format_currency(summary['total_taxes_paid'])
                )

            # Warning if assets depleted
            if summary.get('assets_depleted'):
                st.error(
                    f"**Warning:** Assets are projected to be depleted by year {int(summary['depletion_year'])}!")
            else:
                st.success(
                    "**Good news:** Assets are projected to last through the forecast period!")
            
            # Export Reports section
            st.markdown("---")
            st.subheader("Export Reports")
            
            col_exp1, col_exp2 = st.columns(2)
            
            with col_exp1:
                # Generate PDF report
                if st.button("Generate PDF Report", use_container_width=True):
                    with st.spinner("Generating professional PDF report..."):
                        try:
                            # Get scenario data from session state
                            params = st.session_state.get('current_params', {})
                            
                            # Prepare data for report
                            people_data = [
                                {
                                    'name': p.name,
                                    'age': p.age,
                                    'retirement_age': p.retirement_age,
                                    'current_income': p.current_income,
                                    'annual_rsu_vesting': p.annual_rsu_vesting,
                                    'income_growth_rate': p.income_growth_rate,
                                    'retirement_income': p.retirement_income
                                }
                                for p in params.get('people', [])
                            ]
                            
                            financial_data = {
                                'initial_assets': params.get('initial_assets', 0),
                                'annual_expenses': params.get('annual_expenses', 0),
                                'expense_growth_rate': params.get('expense_growth', 0),
                                'additional_contributions': params.get('additional_contributions', 0),
                                'account_balances': params.get('account_balances'),
                                'contribution_allocation': params.get('contribution_allocation')
                            }
                            
                            investment_data = {
                                'investment_return_rate': params.get('investment_return', 0.07),
                                'inflation_rate': params.get('inflation_rate', 0.025)
                            }
                            
                            tax_data = {
                                'state': params.get('state', 'California')
                            }
                            
                            ss_data = {
                                'age': params.get('ss_age', 67),
                                'benefit': params.get('ss_benefit', 0)
                            }
                            
                            # Generate report
                            report_gen = RetirementReportGenerator()
                            pdf_bytes = report_gen.generate_report(
                                scenario_name=st.session_state.get('scenario_name', 'My Retirement Plan'),
                                people=people_data,
                                financial=financial_data,
                                investment=investment_data,
                                taxes=tax_data,
                                social_security=ss_data,
                                forecast_years=params.get('forecast_years', 50),
                                summary=summary,
                                forecast_df=forecast_df
                            )
                            
                            # Store in session state for download
                            st.session_state['pdf_report'] = pdf_bytes
                            st.success("PDF report generated successfully!")
                        except Exception as e:
                            st.error(f"Error generating report: {str(e)}")
                
                # Download button (only show if PDF is generated)
                if 'pdf_report' in st.session_state:
                    st.download_button(
                        label="Download PDF Report",
                        data=st.session_state['pdf_report'],
                        file_name=f"{st.session_state.get('scenario_name', 'retirement').replace(' ', '_').lower()}_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
            
            with col_exp2:
                # CSV export (existing functionality)
                csv = forecast_df.to_csv(index=False)
                st.download_button(
                    label="Download Data as CSV",
                    data=csv,
                    file_name=f"{st.session_state.get('scenario_name', 'retirement').replace(' ', '_').lower()}_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            st.markdown("---")

            # Visualizations
            st.subheader("Wealth Over Time")

            # Create tabs for different views - add Account Composition if
            # using account types
            has_account_breakdown = 'Traditional_401k' in forecast_df.columns

            if has_account_breakdown:
                tab1, tab2, tab3, tab4, tab5 = st.tabs(
                    ["Assets", "Account Composition", "Income & Expenses", "Cash Flow", "Detailed Data"])
            else:
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["Assets", "Income & Expenses", "Cash Flow", "Detailed Data"])
                tab5 = None
            
            with tab1:
                # Assets chart (Nominal and Real)
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=forecast_df['Year'],
                    y=forecast_df['Assets (Nominal)'],
                    name='Assets (Nominal)',
                    line=dict(color='#1f77b4', width=3),
                    fill='tozeroy',
                    fillcolor='rgba(31, 119, 180, 0.2)'
                ))

                fig.add_trace(go.Scatter(
                    x=forecast_df['Year'],
                    y=forecast_df['Assets (Real)'],
                    name='Assets (Inflation-Adjusted)',
                    line=dict(color='#ff7f0e', width=3, dash='dash')
                ))

                fig.update_layout(
                    title="Asset Growth Projection",
                    xaxis_title="Year",
                    yaxis_title="Assets ($)",
                    hovermode='x unified',
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

                fig.update_yaxes(tickformat='$,.0f')

                st.plotly_chart(fig, use_container_width=True)

                # Add area chart showing asset composition
                st.markdown("**Asset Accumulation Phase**")

                # Identify working vs retirement years
                working_df = forecast_df[forecast_df['Working']]
                retired_df = forecast_df[forecast_df['Working'] == False]

                col1, col2 = st.columns(2)

                with col1:
                    if not working_df.empty:
                        st.metric("Assets at Start of Retirement", format_currency(
                            retired_df.iloc[0]['Assets (Nominal)'] if not retired_df.empty else working_df.iloc[-1]['Assets (Nominal)']))

                with col2:
                    if not retired_df.empty:
                        st.metric(
                            "Years of Assets in Retirement",
                            f"{len(retired_df)} years"
                        )

            # Account Composition Tab (if using account types)
            if has_account_breakdown and tab5:
                with tab2:
                    st.markdown("**Asset Allocation by Account Type**")

                    # Stacked area chart
                    fig_accounts = go.Figure()

                    # Add each account type as a layer
                    account_types = [
                        ('Traditional_401k', 'Traditional 401k', '#E74C3C'),
                        ('Traditional_IRA', 'Traditional IRA', '#C0392B'),
                        ('Roth_401k', 'Roth 401k', '#27AE60'),
                        ('Roth_IRA', 'Roth IRA', '#229954'),
                        ('Taxable', 'Taxable Brokerage', '#3498DB'),
                        ('HSA', 'HSA', '#9B59B6')
                    ]

                    for col_name, display_name, color in account_types:
                        if col_name in forecast_df.columns and forecast_df[col_name].sum(
                        ) > 0:
                            fig_accounts.add_trace(go.Scatter(
                                x=forecast_df['Year'],
                                y=forecast_df[col_name],
                                name=display_name,
                                stackgroup='one',
                                fillcolor=color,
                                mode='none'
                            ))

                    fig_accounts.update_layout(
                        title="Account Composition Over Time",
                        xaxis_title="Year",
                        yaxis_title="Balance ($)",
                        hovermode='x unified',
                        height=500,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )

                    fig_accounts.update_yaxes(tickformat='$,.0f')

                    st.plotly_chart(fig_accounts, use_container_width=True)

                    # Show tax efficiency benefits
                    withdrawal_tax_total = forecast_df['Withdrawal Tax'].sum(
                    ) if 'Withdrawal Tax' in forecast_df.columns else 0

                    if withdrawal_tax_total > 0:
                        st.markdown("**Tax-Efficient Withdrawal Benefits**")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(
                                "Total Withdrawal Taxes Paid",
                                format_currency(withdrawal_tax_total),
                                help="Taxes paid on retirement withdrawals using optimal strategy")
                        with col2:
                            # Estimate suboptimal (if all from Traditional)
                            total_withdrawals = forecast_df['Withdrawal'].sum()
                            if total_withdrawals > 0:
                                avg_rate = withdrawal_tax_total / total_withdrawals if total_withdrawals > 0 else 0
                                st.metric(
                                    "Effective Withdrawal Tax Rate",
                                    f"{avg_rate*100:.1f}%",
                                    help="Average tax rate on withdrawals"
                                )

                    # Current allocation pie chart
                    st.markdown("**Current Allocation**")

                    latest_year = forecast_df.iloc[-1]
                    account_data = []

                    for col_name, display_name, color in account_types:
                        if col_name in forecast_df.columns:
                            balance = latest_year[col_name]
                            if balance > 0:
                                account_data.append({
                                    'Account': display_name,
                                    'Balance': balance,
                                    'Color': color
                                })

                    if account_data:
                        fig_pie = go.Figure(
                            data=[
                                go.Pie(
                                    labels=[
                                        d['Account'] for d in account_data], values=[
                                        d['Balance'] for d in account_data], marker=dict(
                                        colors=[
                                            d['Color'] for d in account_data]), hole=0.3)])

                        fig_pie.update_layout(
                            title=f"Final Year ({int(latest_year['Year'])}) Asset Allocation", height=400)

                        st.plotly_chart(fig_pie, use_container_width=True)
            
            # Assign tab variables based on whether we have account breakdown
            if has_account_breakdown and tab5:
                tab_income = tab3
                tab_cashflow = tab4
                tab_data = tab5
            else:
                tab_income = tab2
                tab_cashflow = tab3
                tab_data = tab4

            with tab_income:
                # Income and Expenses chart with RSU breakdown
                fig = go.Figure()

                # Stack cash income and RSU vesting
                fig.add_trace(go.Bar(
                    x=forecast_df['Year'],
                    y=forecast_df['Cash Income'],
                    name='Cash Income',
                    marker_color='#27ae60',
                    hovertemplate='Cash Income: $%{y:,.0f}<extra></extra>'
                ))

                if 'RSU Vesting' in forecast_df.columns and forecast_df['RSU Vesting'].sum(
                ) > 0:
                    fig.add_trace(go.Bar(
                        x=forecast_df['Year'],
                        y=forecast_df['RSU Vesting'],
                        name='RSU Vesting (taxable)',
                        marker_color='#3498db',
                        hovertemplate='RSU Vesting: $%{y:,.0f}<extra></extra>'
                    ))

                fig.add_trace(go.Bar(
                    x=forecast_df['Year'],
                    y=forecast_df['Expenses'],
                    name='Expenses',
                    marker_color='#e74c3c',
                    hovertemplate='Expenses: $%{y:,.0f}<extra></extra>'
                ))

                fig.add_trace(go.Bar(
                    x=forecast_df['Year'],
                    y=forecast_df['Total Tax'],
                    name='Taxes',
                    marker_color='#95a5a6',
                    hovertemplate='Taxes: $%{y:,.0f}<extra></extra>'
                ))

                fig.update_layout(
                    title="Income, Expenses, and Taxes",
                    xaxis_title="Year",
                    yaxis_title="Amount ($)",
                    barmode='group',
                    hovermode='x unified',
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

                fig.update_yaxes(tickformat='$,.0f')

                st.plotly_chart(fig, use_container_width=True)

            # Show RSU statistics if applicable
            if 'RSU Vesting' in forecast_df.columns:
                total_rsu_vested = forecast_df['RSU Vesting'].sum()

                if total_rsu_vested > 0:
                    st.markdown("**RSU Vesting Summary**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "Total RSU Vesting Income",
                            format_currency(total_rsu_vested),
                            help="Total RSU income over working years"
                        )
                    with col2:
                        working_years = len(
                            forecast_df[forecast_df['RSU Vesting'] > 0])
                        avg_annual = total_rsu_vested / working_years if working_years > 0 else 0
                        st.metric(
                            "Average Annual RSU Income",
                            format_currency(avg_annual),
                            f"{working_years} years"
                        )

                # Tax efficiency metrics
                total_income = forecast_df['Total Income'].sum()
                total_tax = forecast_df['Total Tax'].sum()
                effective_rate = total_tax / total_income if total_income > 0 else 0

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Total Lifetime Income",
                        format_currency(total_income)
                    )
                with col2:
                    st.metric(
                        "Effective Tax Rate",
                        format_percentage(effective_rate)
                    )

            with tab_cashflow:
                # Cash flow chart
                fig = go.Figure()

                # Color code positive and negative cash flow
                colors = ['#2ecc71' if x >=
                          0 else '#e74c3c' for x in forecast_df['Cash Flow']]

                fig.add_trace(go.Bar(
                    x=forecast_df['Year'],
                    y=forecast_df['Cash Flow'],
                    name='Net Cash Flow',
                    marker_color=colors
                ))

                fig.add_trace(go.Scatter(
                    x=forecast_df['Year'],
                    y=forecast_df['Investment Gains'],
                    name='Investment Gains',
                    line=dict(color='#9b59b6', width=2),
                    mode='lines'
                ))

                fig.update_layout(
                    title="Annual Cash Flow and Investment Gains",
                    xaxis_title="Year",
                    yaxis_title="Amount ($)",
                    hovermode='x unified',
                    height=500,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

                fig.update_yaxes(tickformat='$,.0f')

                st.plotly_chart(fig, use_container_width=True)

                # Calculate cumulative investment gains
                total_gains = forecast_df['Investment Gains'].sum()
                total_contributions = initial_assets + \
                    (additional_contributions * len(forecast_df[forecast_df['Working']]))

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Total Investment Gains",
                        format_currency(total_gains)
                    )
                with col2:
                    st.metric(
                        "Total Contributions",
                        format_currency(total_contributions)
                    )

            with tab_data:
                # Detailed data table
                st.subheader("Detailed Year-by-Year Projection")

                # Format the dataframe for display
                display_df = forecast_df.copy()
                display_df['Year'] = display_df['Year'].astype(int)
                display_df['Age'] = display_df['Age'].astype(int)

                # Format currency columns (all monetary values without
                # decimals)
                currency_cols = [
                    'Total Income',
                    'Cash Income',
                    'RSU Vesting',
                    'Ordinary Income',
                    'Social Security',
                    'Expenses',
                    'Total Tax',
                    'Withdrawal Tax',
                    'Net Income',
                    'Cash Flow',
                    'Investment Gains',
                    'Capital Gains',
                    'Withdrawal',
                    'Assets (Nominal)',
                    'Assets (Real)',
                    'Real Expenses',
                    'Real Income',
                    'Traditional_401k',
                    'Traditional_IRA',
                    'Roth_401k',
                    'Roth_IRA',
                    'Taxable',
                    'HSA']

                for col in currency_cols:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(
                            lambda x: f"${x:,.0f}")

                # Format Working column to be more readable
                if 'Working' in display_df.columns:
                    display_df['Working'] = display_df['Working'].apply(
                        lambda x: 'Yes' if x else 'No')

                # Display table with formatting
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    height=500
                )


if __name__ == "__main__":
    main()
