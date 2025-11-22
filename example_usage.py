"""
Example usage of the retirement calculator (programmatic access)
This demonstrates how to use the calculator without the Streamlit UI.
"""

from retirement_calculator import RetirementCalculator, Person
from tax_calculator import TaxCalculator

def example_single_person():
    """Example: Single person retirement planning."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Single Person (All Cash)")
    print("="*60)
    
    # Create person
    person = Person(
        name="Sarah",
        age=28,
        retirement_age=65,
        current_income=85000,
        income_growth_rate=0.035,  # 3.5% annual raises
        retirement_income=0,
        annual_rsu_vesting=0  # No RSUs
    )
    
    # Create calculator
    calculator = RetirementCalculator(
        people=[person],
        initial_assets=50000,
        annual_expenses=55000,
        expense_growth_rate=0.03,
        investment_return_rate=0.08,
        state="New York",
        additional_contributions=20000,
        social_security_age=67,
        social_security_benefit=28000,
        inflation_rate=0.025
    )
    
    # Calculate forecast
    forecast = calculator.calculate_forecast(years=50)
    summary = calculator.calculate_summary_metrics(forecast)
    
    # Display results
    print(f"\nPerson: {person.name}, Age {person.age}")
    print(f"Current Income: ${person.current_income:,.0f}")
    print(f"Starting Assets: ${calculator.initial_assets:,.0f}")
    print(f"Annual Savings: ${calculator.additional_contributions:,.0f}")
    print(f"\nRetirement Summary:")
    print(f"  Retirement year: {summary['retirement_year']}")
    print(f"  Assets at retirement: ${summary['retirement_assets']:,.0f}")
    print(f"  Peak assets: ${summary['peak_assets']:,.0f} (year {summary['peak_year']})")
    print(f"  Final assets: ${summary['final_assets']:,.0f} (age {summary['final_age']})")
    print(f"  Total taxes paid: ${summary['total_taxes_paid']:,.0f}")
    
    if not summary['assets_depleted']:
        print(f"\n✓ Success! Assets last through age {int(summary['final_age'])}")
    else:
        print(f"\n⚠️  Warning: Assets depleted in year {summary['depletion_year']}")


def example_married_couple():
    """Example: Married couple with different retirement ages."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Married Couple")
    print("="*60)
    
    # Create two people
    person1 = Person(
        name="John",
        age=40,
        retirement_age=67,
        current_income=120000,
        income_growth_rate=0.03,
        retirement_income=0
    )
    
    person2 = Person(
        name="Jane",
        age=38,
        retirement_age=65,
        current_income=95000,
        income_growth_rate=0.035,
        retirement_income=15000  # Part-time consulting in retirement
    )
    
    # Create calculator
    calculator = RetirementCalculator(
        people=[person1, person2],
        initial_assets=350000,
        annual_expenses=100000,
        expense_growth_rate=0.03,
        investment_return_rate=0.075,
        state="California",
        additional_contributions=35000,
        social_security_age=67,
        social_security_benefit=50000,  # Combined benefit
        inflation_rate=0.025
    )
    
    # Calculate forecast
    forecast = calculator.calculate_forecast(years=50)
    summary = calculator.calculate_summary_metrics(forecast)
    
    # Display results
    print(f"\nCouple: {person1.name} (age {person1.age}) and {person2.name} (age {person2.age})")
    print(f"Combined Income: ${person1.current_income + person2.current_income:,.0f}")
    print(f"Starting Assets: ${calculator.initial_assets:,.0f}")
    print(f"Annual Expenses: ${calculator.annual_expenses:,.0f}")
    print(f"\nRetirement Summary:")
    print(f"  First retirement year: {summary['retirement_year']} ({person2.name})")
    print(f"  Assets at first retirement: ${summary['retirement_assets']:,.0f}")
    print(f"  Peak assets: ${summary['peak_assets']:,.0f} (year {summary['peak_year']})")
    print(f"  Final assets: ${summary['final_assets']:,.0f}")
    print(f"  Total investment gains: ${summary['total_investment_gains']:,.0f}")
    print(f"  Total taxes paid: ${summary['total_taxes_paid']:,.0f}")
    
    # Calculate savings rate during working years
    working_years = forecast[forecast['Working'] == True]
    if not working_years.empty:
        avg_income = working_years['Total Income'].mean()
        avg_savings = working_years['Cash Flow'].mean()
        savings_rate = (avg_savings / avg_income) * 100
        print(f"\nAverage savings rate (working years): {savings_rate:.1f}%")
    
    if not summary['assets_depleted']:
        print(f"\n✓ Success! Assets last through the forecast period")
        print(f"  Inflation-adjusted final assets: ${forecast.iloc[-1]['Assets (Real)']:,.0f}")
    else:
        print(f"\n⚠️  Warning: Assets depleted in year {summary['depletion_year']}")


def example_tax_comparison():
    """Example: Compare taxes across different states."""
    print("\n" + "="*60)
    print("EXAMPLE 3: State Tax Comparison")
    print("="*60)
    
    income = 150000
    capital_gains = 30000
    
    states = ['California', 'Texas', 'Florida', 'New York', 'Colorado']
    
    print(f"\nTax comparison for:")
    print(f"  Ordinary Income: ${income:,.0f}")
    print(f"  Capital Gains: ${capital_gains:,.0f}")
    print(f"  Filing Status: Married Filing Jointly")
    print(f"\n{'State':<15} {'Federal':<12} {'State':<12} {'FICA':<12} {'Total':<12} {'Effective %'}")
    print("-" * 75)
    
    for state in states:
        total_tax, breakdown = TaxCalculator.calculate_total_tax(
            ordinary_income=income,
            capital_gains=capital_gains,
            state=state,
            filing_jointly=True,
            age=45,
            is_working=True
        )
        
        effective_rate = (total_tax / (income + capital_gains)) * 100
        
        print(f"{state:<15} ${breakdown['federal_income']:>10,.0f} ${breakdown['state']:>10,.0f} "
              f"${breakdown['fica']:>10,.0f} ${total_tax:>10,.0f} {effective_rate:>8.2f}%")


def example_early_retirement():
    """Example: Early retirement (FIRE movement)."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Early Retirement Planning (FIRE)")
    print("="*60)
    
    # High savings rate scenario
    person = Person(
        name="Alex",
        age=25,
        retirement_age=45,  # Retire at 45!
        current_income=100000,
        income_growth_rate=0.04,
        retirement_income=0
    )
    
    calculator = RetirementCalculator(
        people=[person],
        initial_assets=25000,
        annual_expenses=40000,  # Low expenses (60% savings rate initially)
        expense_growth_rate=0.02,  # Keep expenses low
        investment_return_rate=0.08,
        state="Washington",  # No state income tax
        additional_contributions=0,  # Will save the difference automatically
        social_security_age=67,
        social_security_benefit=25000,
        inflation_rate=0.025
    )
    
    forecast = calculator.calculate_forecast(years=60)
    summary = calculator.calculate_summary_metrics(forecast)
    
    print(f"\nEarly Retirement Plan:")
    print(f"  Current age: {person.age}")
    print(f"  Target retirement age: {person.retirement_age}")
    print(f"  Years to retirement: {person.retirement_age - person.age}")
    print(f"  Starting salary: ${person.current_income:,.0f}")
    print(f"  Annual expenses: ${calculator.annual_expenses:,.0f}")
    print(f"  Initial savings rate: {((person.current_income - calculator.annual_expenses) / person.current_income) * 100:.1f}%")
    
    print(f"\nProjected Outcome:")
    if summary['retirement_assets']:
        print(f"  Assets at age {person.retirement_age}: ${summary['retirement_assets']:,.0f}")
        print(f"  Peak assets: ${summary['peak_assets']:,.0f} (age {summary['final_age']})")
        
        # Calculate 4% rule sustainability
        retirement_spending = forecast[forecast['Year'] == summary['retirement_year']]['Expenses'].values[0]
        safe_withdrawal = summary['retirement_assets'] * 0.04
        
        print(f"\n  Retirement spending need: ${retirement_spending:,.0f}/year")
        print(f"  4% safe withdrawal amount: ${safe_withdrawal:,.0f}/year")
        
        if safe_withdrawal >= retirement_spending:
            print(f"  ✓ Passes the 4% rule test!")
        else:
            shortfall = retirement_spending - safe_withdrawal
            print(f"  ⚠️  Shortfall: ${shortfall:,.0f}/year")
    
    if not summary['assets_depleted']:
        print(f"\n✓ Assets last through age {int(summary['final_age'])}")
    else:
        print(f"\n⚠️  Assets depleted at age {person.age + (summary['depletion_year'] - 2024)}")


def example_tech_worker_with_rsus():
    """Example: Tech worker with significant RSU compensation."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Tech Worker with RSU Compensation")
    print("="*60)
    
    # Tech worker with RSUs
    person = Person(
        name="Alex",
        age=32,
        retirement_age=60,
        current_income=160000,  # Cash salary
        income_growth_rate=0.06,  # 6% annual growth (tech industry)
        retirement_income=0,
        annual_rsu_vesting=90000  # Annual RSU vesting
    )
    
    calculator = RetirementCalculator(
        people=[person],
        initial_assets=200000,
        annual_expenses=90000,
        expense_growth_rate=0.03,
        investment_return_rate=0.08,
        state="California",
        additional_contributions=0,  # RSUs provide additional savings
        social_security_age=67,
        social_security_benefit=35000,
        inflation_rate=0.025
    )
    
    forecast = calculator.calculate_forecast(years=45)
    summary = calculator.calculate_summary_metrics(forecast)
    
    # RSU metrics
    total_rsu_vested = forecast['RSU Vesting'].sum()
    total_cash = forecast['Cash Income'].sum()
    
    print(f"\nTech Worker Profile:")
    print(f"  Cash Salary: ${person.current_income:,.0f}")
    print(f"  Annual RSU Vesting: ${person.annual_rsu_vesting:,.0f}")
    print(f"  Total Comp: ${person.current_income + person.annual_rsu_vesting:,.0f}")
    
    print(f"\nLifetime Income:")
    print(f"  Total Cash Income: ${total_cash:,.0f}")
    print(f"  Total RSU Vesting: ${total_rsu_vested:,.0f}")
    print(f"  RSU as % of Income: {(total_rsu_vested / (total_cash + total_rsu_vested) * 100):.1f}%")
    
    print(f"\nRetirement Outcome:")
    print(f"  Retirement Age: {person.retirement_age}")
    print(f"  Assets at Retirement: ${summary['retirement_assets']:,.0f}")
    print(f"  Peak Assets: ${summary['peak_assets']:,.0f}")
    print(f"  Final Assets: ${summary['final_assets']:,.0f} (age {summary['final_age']})")
    
    if not summary['assets_depleted']:
        print(f"\n✓ Successfully funded retirement!")
        print(f"  RSU vesting contributed ${total_rsu_vested:,.0f} to wealth accumulation")
    else:
        print(f"\n⚠️  Assets depleted in year {summary['depletion_year']}")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("RETIREMENT CALCULATOR - EXAMPLE USAGE")
    print("="*60)
    
    example_single_person()
    example_married_couple()
    example_tax_comparison()
    example_early_retirement()
    example_tech_worker_with_rsus()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
    print("\nTo run the interactive Streamlit app:")
    print("  streamlit run retirement_app.py")
    print("\n💡 Feature: RSU/Equity Compensation Support!")
    print("   - Enter annual RSU vesting amount")
    print("   - RSUs taxed as ordinary income")
    print("   - Vesting stops at retirement (unvested shares forfeited)")
    print("   - Simple and intuitive modeling")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

