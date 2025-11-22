"""
Retirement forecasting engine.
Calculates year-by-year projections of wealth, income, expenses, and taxes.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
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
        contribution_allocation: Optional[Dict[str, float]] = None
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
            current_year = 2024 + year
            
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

