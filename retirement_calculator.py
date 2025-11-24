"""
Retirement forecasting engine.
Calculates year-by-year projections of wealth, income, expenses, and taxes.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
from tax_calculator import TaxCalculator
from account_types import AccountPortfolio, AccountType, WithdrawalStrategy


class Person:
    """Represents an individual in the household."""
    
    def __init__(
        self,
        name: str,
        age: int,
        retirement_age: int,
        current_income: float,
        income_growth_rate: float = 0.03,
        retirement_income: float = 0.0,
        annual_rsu_vesting: float = 0.0
    ):
        """
        Initialize a person.
        
        Args:
            name: Person's name
            age: Current age
            retirement_age: Age at retirement
            current_income: Annual cash salary/wages
            income_growth_rate: Annual growth rate for income
            retirement_income: Income in retirement (pensions, etc.)
            annual_rsu_vesting: Annual RSU vesting amount (taxed as income, stops at retirement)
        """
        self.name = name
        self.age = age
        self.retirement_age = retirement_age
        self.current_income = current_income
        self.income_growth_rate = income_growth_rate
        self.retirement_income = retirement_income
        self.annual_rsu_vesting = annual_rsu_vesting
    
    def get_income(self, year_offset: int) -> tuple[float, float, bool]:
        """
        Get income for a given year offset.
        
        Args:
            year_offset: Years from current year (0 = current year)
            
        Returns:
            Tuple of (cash_income, rsu_vesting, is_working)
        """
        current_age = self.age + year_offset
        
        if current_age < self.retirement_age:
            # Still working, apply income growth
            cash = self.current_income * ((1 + self.income_growth_rate) ** year_offset)
            rsu_vesting = self.annual_rsu_vesting * ((1 + self.income_growth_rate) ** year_offset)
            return cash, rsu_vesting, True
        else:
            # Retired - no more salary or RSU vesting
            return self.retirement_income, 0.0, False


class RetirementCalculator:
    """Main calculator for retirement forecasting."""
    
    def __init__(
        self,
        people: List[Person],
        initial_assets: float,
        annual_expenses: float,
        expense_growth_rate: float,
        investment_return_rate: float,
        state: str,
        additional_contributions: float = 0.0,
        social_security_age: int = 67,
        social_security_benefit: float = 0.0,
        inflation_rate: float = 0.025,
        account_balances: Optional[Dict[str, float]] = None,
        contribution_allocation: Optional[Dict[str, float]] = None,
        one_time_expenses: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize the retirement calculator.
        
        Args:
            people: List of Person objects
            initial_assets: Starting investment assets
            annual_expenses: Annual living expenses
            expense_growth_rate: Annual expense growth rate
            investment_return_rate: Expected annual return on investments
            state: State for tax calculations
            additional_contributions: Annual additional savings
            social_security_age: Age to start receiving Social Security
            social_security_benefit: Annual Social Security benefit
            inflation_rate: Expected inflation rate
            account_balances: Dict of initial balances by account type (e.g., {'traditional_401k': 100000})
            contribution_allocation: Dict of contribution percentages by account type (must sum to 1.0)
            one_time_expenses: List of one-time expenses (e.g., [{'year': 2030, 'description': 'New Car', 'amount': 45000}])
        """
        self.people = people
        self.initial_assets = initial_assets
        self.annual_expenses = annual_expenses
        self.expense_growth_rate = expense_growth_rate
        self.investment_return_rate = investment_return_rate
        self.state = state
        self.additional_contributions = additional_contributions
        self.social_security_age = social_security_age
        self.social_security_benefit = social_security_benefit
        self.inflation_rate = inflation_rate
        self.filing_jointly = len(people) > 1
        
        # Initialize account portfolio
        self.portfolio = AccountPortfolio()
        
        if account_balances:
            # User specified account breakdown
            for account_name, balance in account_balances.items():
                account_type = AccountType(account_name)
                # For taxable accounts, assume cost basis = 80% of balance initially
                cost_basis = balance * 0.8 if account_type == AccountType.TAXABLE else balance
                self.portfolio.add_account(account_type, balance, cost_basis)
        else:
            # Default: all assets in taxable account
            self.portfolio.add_account(AccountType.TAXABLE, initial_assets, initial_assets * 0.8)
        
        # Contribution allocation (where new savings go)
        self.contribution_allocation = contribution_allocation or {'taxable': 1.0}
        
        # Store account balances for Monte Carlo simulation
        self.account_balances = account_balances
        
        # One-time expenses (e.g., car purchases, major repairs)
        # Format: [{'year': 2030, 'description': 'New Car', 'amount': 45000}, ...]
        self.one_time_expenses = one_time_expenses or []
    
    def calculate_forecast(self, years: int = 50) -> pd.DataFrame:
        """
        Calculate year-by-year retirement forecast with account-specific tax treatment.
        
        Args:
            years: Number of years to forecast
            
        Returns:
            DataFrame with yearly projections including per-account balances
        """
        results = []
        
        # Use portfolio for multi-account tracking
        portfolio = self.portfolio
        
        for year in range(years):
            current_year = datetime.now().year + year
            
            # Calculate total income from all people
            total_cash_income = 0.0
            total_rsu_vesting = 0.0
            anyone_working = False
            oldest_age = 0
            
            for person in self.people:
                cash_income, rsu_vesting, is_working = person.get_income(year)
                total_cash_income += cash_income
                total_rsu_vesting += rsu_vesting
                if is_working:
                    anyone_working = True
                oldest_age = max(oldest_age, person.age + year)
            
            # Total ordinary income includes cash + RSUs (both taxed as ordinary income)
            total_ordinary_income = total_cash_income + total_rsu_vesting
            
            # Add Social Security if eligible
            social_security_income = 0.0
            if oldest_age >= self.social_security_age:
                social_security_income = self.social_security_benefit
                total_ordinary_income += social_security_income
            
            # Calculate expenses for this year
            expenses = self.annual_expenses * ((1 + self.expense_growth_rate) ** year)
            
            # Add any one-time expenses for this year
            for expense in self.one_time_expenses:
                if expense.get('year') == current_year:
                    expenses += expense.get('amount', 0)
            
            # Get total assets before growth
            assets_before_growth = portfolio.get_total_balance()
            
            # Apply investment returns to all accounts
            portfolio.apply_growth(self.investment_return_rate)
            investment_gains = portfolio.get_total_balance() - assets_before_growth
            
            # Calculate taxes on ordinary income (before withdrawal strategy)
            _, tax_breakdown = TaxCalculator.calculate_total_tax(
                ordinary_income=total_ordinary_income,
                capital_gains=0.0,  # Withdrawal tax calculated separately
                state=self.state,
                filing_jointly=self.filing_jointly,
                age=oldest_age,
                is_working=anyone_working
            )
            
            total_tax = tax_breakdown['total']
            
            # Net income after taxes
            net_income = total_ordinary_income - total_tax
            
            # Cash flow: net income + contributions - expenses
            cash_flow = net_income + self.additional_contributions - expenses
            
            # Handle contributions or withdrawals
            withdrawal = 0.0
            withdrawal_tax = 0.0
            capital_gains = 0.0
            withdrawal_by_account = {}
            
            if cash_flow > 0:
                # Positive cash flow: deposit to accounts based on allocation
                for account_name, allocation_pct in self.contribution_allocation.items():
                    if allocation_pct > 0:
                        try:
                            account_type = AccountType(account_name)
                            deposit_amount = cash_flow * allocation_pct
                            portfolio.deposit(account_type, deposit_amount)
                        except:
                            # Fallback: deposit to taxable if account type not recognized
                            portfolio.deposit(AccountType.TAXABLE, cash_flow * allocation_pct)
            
            elif cash_flow < 0:
                # Negative cash flow: tax-efficient withdrawal from portfolio
                amount_needed = -cash_flow
                
                withdrawal_by_account, withdrawal_tax = WithdrawalStrategy.calculate_withdrawal(
                    portfolio,
                    amount_needed,
                    oldest_age,
                    total_ordinary_income,
                    self.filing_jointly
                )
                
                # Apply withdrawals to portfolio
                for account_type, amount in withdrawal_by_account.items():
                    current_balance = portfolio.get_balance(account_type)
                    portfolio.update_balance(account_type, current_balance - amount)
                    withdrawal += amount
                
                # Add withdrawal tax to total tax
                total_tax += withdrawal_tax
                
                # Calculate capital gains (from taxable account withdrawals)
                if AccountType.TAXABLE in withdrawal_by_account:
                    taxable_withdrawal = withdrawal_by_account[AccountType.TAXABLE]
                    taxable_balance_before = portfolio.get_balance(AccountType.TAXABLE) + taxable_withdrawal
                    cost_basis = portfolio.get_cost_basis(AccountType.TAXABLE)
                    if taxable_balance_before > 0:
                        gains_ratio = max(0, (taxable_balance_before - cost_basis) / taxable_balance_before)
                        capital_gains = taxable_withdrawal * gains_ratio
            
            # Get final total assets
            assets = portfolio.get_total_balance()
            
            # Ensure assets don't go negative
            if assets < 0:
                assets = 0
            
            # Calculate real values (inflation-adjusted)
            real_assets = assets / ((1 + self.inflation_rate) ** year)
            real_expenses = expenses / ((1 + self.inflation_rate) ** year)
            real_income = total_ordinary_income / ((1 + self.inflation_rate) ** year)
            
            # Get individual account balances
            traditional_401k = portfolio.get_balance(AccountType.TRADITIONAL_401K)
            traditional_ira = portfolio.get_balance(AccountType.TRADITIONAL_IRA)
            roth_401k = portfolio.get_balance(AccountType.ROTH_401K)
            roth_ira = portfolio.get_balance(AccountType.ROTH_IRA)
            taxable = portfolio.get_balance(AccountType.TAXABLE)
            hsa = portfolio.get_balance(AccountType.HSA)
            
            # Store results
            results.append({
                'Year': current_year,
                'Age': oldest_age,
                'Total Income': total_ordinary_income,
                'Cash Income': total_cash_income - social_security_income,
                'RSU Vesting': total_rsu_vesting,
                'Ordinary Income': total_ordinary_income - social_security_income,
                'Social Security': social_security_income,
                'Expenses': expenses,
                'Total Tax': total_tax,
                'Withdrawal Tax': withdrawal_tax,
                'Net Income': net_income,
                'Cash Flow': cash_flow,
                'Investment Gains': investment_gains,
                'Capital Gains': capital_gains,
                'Withdrawal': withdrawal,
                'Assets (Nominal)': assets,
                'Assets (Real)': real_assets,
                'Real Expenses': real_expenses,
                'Real Income': real_income,
                'Working': anyone_working,
                # Account-specific balances
                'Traditional_401k': traditional_401k,
                'Traditional_IRA': traditional_ira,
                'Roth_401k': roth_401k,
                'Roth_IRA': roth_ira,
                'Taxable': taxable,
                'HSA': hsa
            })
            
            # Stop if assets depleted
            if assets <= 0:
                break
        
        return pd.DataFrame(results)
    
    def calculate_summary_metrics(self, forecast_df: pd.DataFrame) -> Dict:
        """
        Calculate summary metrics from forecast.
        
        Args:
            forecast_df: Forecast DataFrame
            
        Returns:
            Dictionary of summary metrics
        """
        if forecast_df.empty:
            return {}
        
        # Find retirement year (when no one is working)
        retirement_rows = forecast_df[forecast_df['Working'] == False]
        retirement_year = retirement_rows.iloc[0]['Year'] if not retirement_rows.empty else None
        retirement_assets = retirement_rows.iloc[0]['Assets (Nominal)'] if not retirement_rows.empty else None
        
        # Peak assets
        peak_assets = forecast_df['Assets (Nominal)'].max()
        peak_year = forecast_df.loc[forecast_df['Assets (Nominal)'].idxmax(), 'Year']
        
        # Final assets
        final_assets = forecast_df.iloc[-1]['Assets (Nominal)']
        final_year = forecast_df.iloc[-1]['Year']
        final_age = forecast_df.iloc[-1]['Age']
        
        # Total taxes paid
        total_taxes = forecast_df['Total Tax'].sum()
        
        # Total investment gains
        total_gains = forecast_df['Investment Gains'].sum()
        
        # Check if assets depleted
        assets_depleted = final_assets <= 0
        depletion_year = final_year if assets_depleted else None
        
        return {
            'retirement_year': retirement_year,
            'retirement_assets': retirement_assets,
            'peak_assets': peak_assets,
            'peak_year': peak_year,
            'final_assets': final_assets,
            'final_year': final_year,
            'final_age': final_age,
            'total_taxes_paid': total_taxes,
            'total_investment_gains': total_gains,
            'assets_depleted': assets_depleted,
            'depletion_year': depletion_year
        }
    
    def run_monte_carlo_simulation(
        self, 
        years: int = 50, 
        iterations: int = 1000, 
        return_std_dev: float = 0.15
    ) -> Dict:
        """
        Run Monte Carlo simulation with variable investment returns.
        
        Args:
            years: Number of years to forecast
            iterations: Number of simulations to run
            return_std_dev: Standard deviation of returns (default 15%)
            
        Returns:
            Dictionary containing:
                - simulations: List of DataFrames (one per simulation)
                - percentiles: DataFrame with 10th, 50th, 90th percentile assets
                - success_rate: Percentage of simulations where assets last
                - final_assets_distribution: List of final asset values
        """
        np.random.seed(42)  # For reproducibility
        
        simulations = []
        final_assets = []
        success_count = 0
        
        base_return = self.investment_return_rate
        
        for sim in range(iterations):
            # Generate random returns for each year (normal distribution)
            annual_returns = np.random.normal(base_return, return_std_dev, years)
            
            # Temporarily override the investment return rate
            original_return = self.investment_return_rate
            
            # Run simulation with variable returns
            sim_results = []
            assets = self.initial_assets
            portfolio = AccountPortfolio(self.initial_assets, self.account_balances)
            
            for year in range(years):
                current_year = datetime.now().year + year
                
                # Use this year's random return
                year_return = annual_returns[year]
                
                # Run one year of simulation (simplified version)
                # We'll reuse the core logic but with variable returns
                oldest_age = max(person.age + year for person in self.people)
                anyone_working = any(person.age + year < person.retirement_age for person in self.people)
                
                # Calculate income (same logic as main forecast)
                total_cash_income = sum(
                    person.current_income * ((1 + person.income_growth_rate) ** year)
                    if person.age + year < person.retirement_age else person.retirement_income
                    for person in self.people
                )
                
                total_rsu_vesting = sum(
                    person.annual_rsu_vesting * ((1 + person.income_growth_rate) ** year)
                    if person.age + year < person.retirement_age else 0
                    for person in self.people
                )
                
                total_ordinary_income = total_cash_income + total_rsu_vesting
                
                # Social Security
                social_security_income = self.social_security_benefit if oldest_age >= self.social_security_age else 0
                total_ordinary_income += social_security_income
                
                # Expenses
                years_elapsed = year
                expenses = self.annual_expenses * ((1 + self.expense_growth_rate) ** years_elapsed)
                
                # Add one-time expenses
                for expense in self.one_time_expenses:
                    if expense.get('year') == current_year:
                        expenses += expense.get('amount', 0)
                
                # Additional contributions
                additional_contribution = self.additional_contributions if anyone_working else 0
                
                # Calculate taxes (simplified for speed)
                total_tax = 0
                if total_ordinary_income > 0:
                    tax_calc = TaxCalculator(state=self.state)
                    ordinary_income_tax = tax_calc.calculate_income_tax(
                        ordinary_income=total_ordinary_income,
                        capital_gains=0,
                        num_people=len(self.people)
                    )
                    total_tax = ordinary_income_tax
                
                net_income = total_ordinary_income - total_tax
                cash_flow = net_income - expenses + additional_contribution
                
                # Apply investment gains with THIS year's random return
                investment_gains = assets * year_return
                
                # Update assets
                assets = assets + cash_flow + investment_gains
                
                # Store minimal results (just what we need for percentiles)
                sim_results.append({
                    'Year': current_year,
                    'Assets': assets
                })
                
                # Stop if depleted
                if assets <= 0:
                    break
            
            # Store results
            sim_df = pd.DataFrame(sim_results)
            simulations.append(sim_df)
            
            # Track final assets
            if len(sim_df) > 0:
                final_asset_value = sim_df.iloc[-1]['Assets']
                final_assets.append(final_asset_value)
                if final_asset_value > 0:
                    success_count += 1
            else:
                final_assets.append(0)
        
        # Calculate percentiles across all simulations
        # Create a matrix of assets: rows=years, cols=simulations
        max_years = max(len(sim) for sim in simulations)
        asset_matrix = np.zeros((max_years, iterations))
        
        for sim_idx, sim_df in enumerate(simulations):
            for year_idx, row in sim_df.iterrows():
                if year_idx < max_years:
                    asset_matrix[year_idx, sim_idx] = row['Assets']
        
        # Calculate percentiles for each year
        years_list = range(datetime.now().year, datetime.now().year + max_years)
        percentiles_df = pd.DataFrame({
            'Year': years_list,
            'p10': np.percentile(asset_matrix, 10, axis=1),
            'p25': np.percentile(asset_matrix, 25, axis=1),
            'p50': np.percentile(asset_matrix, 50, axis=1),
            'p75': np.percentile(asset_matrix, 75, axis=1),
            'p90': np.percentile(asset_matrix, 90, axis=1)
        })
        
        success_rate = (success_count / iterations) * 100
        
        return {
            'percentiles': percentiles_df,
            'success_rate': success_rate,
            'final_assets_distribution': final_assets,
            'num_simulations': iterations
        }

