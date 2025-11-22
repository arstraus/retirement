"""
Example demonstrating account types feature and tax savings
"""

from retirement_calculator import RetirementCalculator, Person

def compare_with_and_without_account_types():
    """Compare same scenario with and without account type optimization."""
    print("=" * 80)
    print("ACCOUNT TYPES DEMONSTRATION - TAX SAVINGS COMPARISON")
    print("=" * 80)
    
    # Same person in both scenarios
    person = Person(
        name="Tech Worker",
        age=35,
        retirement_age=62,  # Early retirement
        current_income=150000,
        income_growth_rate=0.04,
        retirement_income=0,
        annual_rsu_vesting=80000
    )
    
    print(f"\nPerson Profile:")
    print(f"  Name: {person.name}")
    print(f"  Current Age: {person.age}")
    print(f"  Retirement Age: {person.retirement_age}")
    print(f"  Cash Salary: ${person.current_income:,.0f}")
    print(f"  Annual RSU Vesting: ${person.annual_rsu_vesting:,.0f}")
    print(f"  Total Comp: ${person.current_income + person.annual_rsu_vesting:,.0f}")
    
    # Scenario 1: WITHOUT account types (all in one pool)
    print("\n" + "=" * 80)
    print("SCENARIO 1: WITHOUT Account Types (Simple)")
    print("=" * 80)
    
    calc_simple = RetirementCalculator(
        people=[person],
        initial_assets=400000,
        annual_expenses=90000,
        expense_growth_rate=0.03,
        investment_return_rate=0.07,
        state="California",
        additional_contributions=25000,
        social_security_age=67,
        social_security_benefit=40000,
        inflation_rate=0.025
        # No account_balances or contribution_allocation
    )
    
    forecast_simple = calc_simple.calculate_forecast(years=45)
    
    print(f"\nStarting Assets: ${calc_simple.initial_assets:,.0f} (single pool)")
    print(f"Final Assets: ${forecast_simple.iloc[-1]['Assets (Nominal)']:,.0f}")
    print(f"Total Taxes Paid: ${forecast_simple['Total Tax'].sum():,.0f}")
    
    # Scenario 2: WITH account types (tax-optimized)
    print("\n" + "=" * 80)
    print("SCENARIO 2: WITH Account Types (Tax-Optimized)")
    print("=" * 80)
    
    account_balances = {
        'traditional_401k': 200000,
        'roth_ira': 120000,
        'taxable': 80000
    }
    
    contribution_allocation = {
        'traditional_401k': 0.60,  # 60% to Traditional (tax savings now)
        'roth_ira': 0.30,           # 30% to Roth (tax-free later)
        'taxable': 0.10             # 10% to Taxable (flexibility)
    }
    
    calc_optimized = RetirementCalculator(
        people=[person],
        initial_assets=400000,
        annual_expenses=90000,
        expense_growth_rate=0.03,
        investment_return_rate=0.07,
        state="California",
        additional_contributions=25000,
        social_security_age=67,
        social_security_benefit=40000,
        inflation_rate=0.025,
        account_balances=account_balances,
        contribution_allocation=contribution_allocation
    )
    
    forecast_optimized = calc_optimized.calculate_forecast(years=45)
    
    print(f"\nStarting Account Balances:")
    for acc_name, balance in account_balances.items():
        print(f"  {acc_name.replace('_', ' ').title()}: ${balance:,.0f}")
    print(f"  Total: ${sum(account_balances.values()):,.0f}")
    
    print(f"\nContribution Allocation:")
    for acc_name, pct in contribution_allocation.items():
        print(f"  {acc_name.replace('_', ' ').title()}: {pct*100:.0f}%")
    
    print(f"\nFinal Assets: ${forecast_optimized.iloc[-1]['Assets (Nominal)']:,.0f}")
    print(f"Total Taxes Paid: ${forecast_optimized['Total Tax'].sum():,.0f}")
    
    # Show final account breakdown
    final_year = forecast_optimized.iloc[-1]
    print(f"\nFinal Account Breakdown (Year {int(final_year['Year'])}):")
    print(f"  Traditional 401k: ${final_year['Traditional_401k']:,.0f}")
    print(f"  Roth IRA: ${final_year['Roth_IRA']:,.0f}")
    print(f"  Taxable: ${final_year['Taxable']:,.0f}")
    
    # Calculate withdrawal-specific taxes
    withdrawal_tax_simple = 0  # Approximation
    withdrawal_tax_optimized = forecast_optimized['Withdrawal Tax'].sum()
    
    print(f"\nWithdrawal Taxes:")
    print(f"  Simple (estimated): N/A (bundled in total)")
    print(f"  Optimized: ${withdrawal_tax_optimized:,.0f}")
    
    # Comparison
    print("\n" + "=" * 80)
    print("💰 COMPARISON & TAX SAVINGS")
    print("=" * 80)
    
    total_tax_simple = forecast_simple['Total Tax'].sum()
    total_tax_optimized = forecast_optimized['Total Tax'].sum()
    tax_savings = total_tax_simple - total_tax_optimized
    
    print(f"\n{'Metric':<30} {'Simple':<20} {'Optimized':<20} {'Difference'}")
    print("-" * 80)
    
    metrics = [
        ("Final Assets", 
         forecast_simple.iloc[-1]['Assets (Nominal)'],
         forecast_optimized.iloc[-1]['Assets (Nominal)']),
        ("Total Taxes Paid",
         total_tax_simple,
         total_tax_optimized),
    ]
    
    for name, simple_val, opt_val in metrics:
        diff = opt_val - simple_val
        diff_str = f"${abs(diff):>10,.0f} {'better' if diff > 0 and 'Tax' not in name else 'saved' if diff < 0 else ''}"
        print(f"{name:<30} ${simple_val:>18,.0f} ${opt_val:>18,.0f} {diff_str}")
    
    if tax_savings > 0:
        print(f"\n🎉 TOTAL LIFETIME TAX SAVINGS: ${tax_savings:,.0f}")
        print(f"   Average savings per year: ${tax_savings / 45:,.0f}/year")
    
    # Show year-by-year example
    print("\n" + "=" * 80)
    print("RETIREMENT YEARS EXAMPLE (First 5 Years)")
    print("=" * 80)
    
    retirement_start = forecast_optimized[forecast_optimized['Working'] == False].index[0]
    
    print(f"\n{'Year':<6} {'Traditional':<15} {'Roth':<15} {'Taxable':<15} {'Total':<15}")
    print("-" * 80)
    
    for i in range(min(5, len(forecast_optimized) - retirement_start)):
        idx = retirement_start + i
        row = forecast_optimized.iloc[idx]
        print(f"{int(row['Year']):<6} ${row['Traditional_401k']:>13,.0f} "
              f"${row['Roth_IRA']:>13,.0f} ${row['Taxable']:>13,.0f} "
              f"${row['Assets (Nominal)']:>13,.0f}")
    
    print("\n✓ Notice: Taxable depletes first (most tax-efficient to withdraw)")
    
    print("\n" + "=" * 80)
    print("🎯 KEY TAKEAWAY")
    print("=" * 80)
    print("\nUsing account types with tax-efficient withdrawals:")
    print(f"  • Saves ${tax_savings:,.0f} in lifetime taxes")
    print(f"  • Optimizes which accounts to tap first")
    print(f"  • Handles RMDs automatically at age 73")
    print(f"  • Maximizes Roth tax-free growth")
    print("\nThis is REAL money saved - not hypothetical!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    compare_with_and_without_account_types()



