"""
Account type modeling for different tax treatments.
Traditional 401k/IRA, Roth, Taxable, HSA accounts.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple


class AccountType(Enum):
    """Types of retirement/investment accounts."""
    TRADITIONAL_401K = "traditional_401k"
    TRADITIONAL_IRA = "traditional_ira"
    ROTH_401K = "roth_401k"
    ROTH_IRA = "roth_ira"
    TAXABLE = "taxable"
    HSA = "hsa"


@dataclass
class AccountBalance:
    """Balance for a specific account type."""
    account_type: AccountType
    balance: float
    cost_basis: float  # For taxable accounts (tracks capital gains)
    
    def __post_init__(self):
        """Ensure balance and cost basis are non-negative."""
        self.balance = max(0, self.balance)
        self.cost_basis = max(0, min(self.cost_basis, self.balance))


class AccountPortfolio:
    """Manages multiple account types with different tax treatments."""
    
    def __init__(self):
        """Initialize empty portfolio."""
        self.accounts: Dict[AccountType, AccountBalance] = {}
    
    def add_account(self, account_type: AccountType, balance: float, cost_basis: float = None):
        """
        Add or update an account.
        
        Args:
            account_type: Type of account
            balance: Current balance
            cost_basis: Cost basis (for taxable accounts, defaults to balance)
        """
        if cost_basis is None:
            cost_basis = balance
        
        self.accounts[account_type] = AccountBalance(
            account_type=account_type,
            balance=balance,
            cost_basis=cost_basis
        )
    
    def get_balance(self, account_type: AccountType) -> float:
        """Get balance for specific account type."""
        if account_type in self.accounts:
            return self.accounts[account_type].balance
        return 0.0
    
    def get_total_balance(self) -> float:
        """Get total balance across all accounts."""
        return sum(acc.balance for acc in self.accounts.values())
    
    def get_cost_basis(self, account_type: AccountType) -> float:
        """Get cost basis for specific account (relevant for taxable)."""
        if account_type in self.accounts:
            return self.accounts[account_type].cost_basis
        return 0.0
    
    def update_balance(self, account_type: AccountType, new_balance: float):
        """Update account balance."""
        if account_type in self.accounts:
            self.accounts[account_type].balance = max(0, new_balance)
    
    def update_cost_basis(self, account_type: AccountType, new_basis: float):
        """Update cost basis (for taxable accounts)."""
        if account_type in self.accounts:
            account = self.accounts[account_type]
            account.cost_basis = max(0, min(new_basis, account.balance))
    
    def apply_growth(self, growth_rate: float):
        """Apply investment growth to all accounts."""
        for account in self.accounts.values():
            growth = account.balance * growth_rate
            account.balance += growth
            # Cost basis doesn't change with growth (only contributions)
    
    def deposit(self, account_type: AccountType, amount: float):
        """
        Deposit money into an account.
        
        Args:
            account_type: Type of account
            amount: Amount to deposit
        """
        if amount <= 0:
            return
        
        if account_type not in self.accounts:
            self.add_account(account_type, 0, 0)
        
        account = self.accounts[account_type]
        account.balance += amount
        # Deposits add to cost basis
        account.cost_basis += amount


class WithdrawalStrategy:
    """Determines optimal withdrawal order for tax efficiency."""
    
    @staticmethod
    def calculate_withdrawal(
        portfolio: AccountPortfolio,
        amount_needed: float,
        age: int,
        ordinary_income: float,
        filing_jointly: bool
    ) -> Tuple[Dict[AccountType, float], float]:
        """
        Calculate tax-efficient withdrawals from multiple accounts.
        
        Strategy:
        1. Taxable accounts first (only capital gains taxed)
        2. Traditional accounts (fully taxable as ordinary income)
        3. Roth accounts last (tax-free)
        4. HSA for medical (tax-free)
        
        Args:
            portfolio: Account portfolio
            amount_needed: Amount needed (pre-tax)
            age: Person's age (for RMD calculations)
            ordinary_income: Current ordinary income (affects tax brackets)
            filing_jointly: Tax filing status
            
        Returns:
            Tuple of (withdrawals_by_account, total_tax_on_withdrawals)
        """
        from tax_calculator import TaxCalculator
        
        withdrawals = {}
        remaining_needed = amount_needed
        total_capital_gains = 0
        total_ordinary_withdrawals = 0
        
        # Priority order for tax efficiency
        withdrawal_order = [
            AccountType.TAXABLE,      # Only gains taxed
            AccountType.HSA,           # Tax-free (for medical expenses)
            AccountType.TRADITIONAL_401K,  # Ordinary income tax
            AccountType.TRADITIONAL_IRA,   # Ordinary income tax
            AccountType.ROTH_401K,     # Tax-free
            AccountType.ROTH_IRA       # Tax-free
        ]
        
        # Check for RMDs (Required Minimum Distributions) at age 73+
        if age >= 73:
            rmd_amount = WithdrawalStrategy._calculate_rmd(portfolio, age)
            if rmd_amount > 0:
                # Must take RMD from traditional accounts first
                traditional_types = [AccountType.TRADITIONAL_401K, AccountType.TRADITIONAL_IRA]
                rmd_remaining = rmd_amount
                
                for acc_type in traditional_types:
                    if rmd_remaining <= 0:
                        break
                    
                    available = portfolio.get_balance(acc_type)
                    if available > 0:
                        withdrawal = min(rmd_remaining, available)
                        withdrawals[acc_type] = withdrawals.get(acc_type, 0) + withdrawal
                        total_ordinary_withdrawals += withdrawal
                        rmd_remaining -= withdrawal
                        remaining_needed -= withdrawal
        
        # Withdraw in optimal order
        for account_type in withdrawal_order:
            if remaining_needed <= 0:
                break
            
            available_balance = portfolio.get_balance(account_type)
            if available_balance <= 0:
                continue
            
            # Calculate how much to withdraw from this account
            if account_type == AccountType.TAXABLE:
                # For taxable, estimate tax on gains
                cost_basis = portfolio.get_cost_basis(account_type)
                gains_ratio = max(0, (available_balance - cost_basis) / available_balance) if available_balance > 0 else 0
                
                # Withdraw as much as possible from taxable first
                gross_withdrawal = min(remaining_needed * 1.5, available_balance)  # Buffer for taxes
                capital_gains = gross_withdrawal * gains_ratio
                
                # Estimate capital gains tax
                cg_tax = TaxCalculator.calculate_capital_gains_tax(
                    capital_gains,
                    ordinary_income + total_ordinary_withdrawals,
                    filing_jointly
                )
                
                # Actual amount withdrawn
                net_withdrawal = gross_withdrawal - cg_tax
                
                if net_withdrawal > 0:
                    withdrawals[account_type] = gross_withdrawal
                    total_capital_gains += capital_gains
                    remaining_needed -= net_withdrawal
                    
            elif account_type in [AccountType.TRADITIONAL_401K, AccountType.TRADITIONAL_IRA]:
                # Traditional accounts: fully taxable as ordinary income
                # Need to withdraw more to cover taxes
                
                # Estimate marginal tax rate
                test_income = ordinary_income + total_ordinary_withdrawals + 10000
                test_tax = TaxCalculator.calculate_federal_income_tax(test_income, filing_jointly)
                base_tax = TaxCalculator.calculate_federal_income_tax(ordinary_income + total_ordinary_withdrawals, filing_jointly)
                marginal_rate = (test_tax - base_tax) / 10000
                
                # Gross withdrawal needed to get remaining_needed after tax
                gross_needed = remaining_needed / (1 - marginal_rate)
                gross_withdrawal = min(gross_needed, available_balance)
                
                withdrawals[account_type] = gross_withdrawal
                total_ordinary_withdrawals += gross_withdrawal
                remaining_needed -= gross_withdrawal * (1 - marginal_rate)
                
            elif account_type in [AccountType.ROTH_401K, AccountType.ROTH_IRA, AccountType.HSA]:
                # Tax-free withdrawals
                withdrawal = min(remaining_needed, available_balance)
                withdrawals[account_type] = withdrawal
                remaining_needed -= withdrawal
        
        # Calculate total taxes on withdrawals
        capital_gains_tax = TaxCalculator.calculate_capital_gains_tax(
            total_capital_gains,
            ordinary_income,
            filing_jointly
        ) if total_capital_gains > 0 else 0
        
        ordinary_tax = 0
        if total_ordinary_withdrawals > 0:
            total_income_with = ordinary_income + total_ordinary_withdrawals
            total_income_without = ordinary_income
            tax_with = TaxCalculator.calculate_federal_income_tax(total_income_with, filing_jointly)
            tax_without = TaxCalculator.calculate_federal_income_tax(total_income_without, filing_jointly)
            ordinary_tax = tax_with - tax_without
        
        total_withdrawal_tax = capital_gains_tax + ordinary_tax
        
        return withdrawals, total_withdrawal_tax
    
    @staticmethod
    def _calculate_rmd(portfolio: AccountPortfolio, age: int) -> float:
        """
        Calculate Required Minimum Distribution.
        
        RMDs required at age 73+ (as of 2024 SECURE Act 2.0)
        
        Args:
            portfolio: Account portfolio
            age: Person's age
            
        Returns:
            Required minimum distribution amount
        """
        if age < 73:
            return 0.0
        
        # IRS Uniform Lifetime Table (simplified)
        distribution_period = {
            73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9,
            78: 22.0, 79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5,
            83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2, 87: 14.4,
            88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8,
            93: 10.1, 94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8,
            98: 7.3, 99: 6.8, 100: 6.4
        }.get(age, 6.4)  # Default for age 100+
        
        # RMD only applies to traditional accounts
        traditional_balance = (
            portfolio.get_balance(AccountType.TRADITIONAL_401K) +
            portfolio.get_balance(AccountType.TRADITIONAL_IRA)
        )
        
        return traditional_balance / distribution_period if distribution_period > 0 else 0
    
    @staticmethod
    def get_contribution_tax_benefit(
        amount: float,
        account_type: AccountType,
        ordinary_income: float,
        filing_jointly: bool
    ) -> float:
        """
        Calculate tax benefit of contributing to an account.
        
        Args:
            amount: Contribution amount
            account_type: Type of account
            ordinary_income: Current ordinary income
            filing_jointly: Tax filing status
            
        Returns:
            Tax savings from contribution
        """
        from tax_calculator import TaxCalculator
        
        if account_type in [AccountType.TRADITIONAL_401K, AccountType.TRADITIONAL_IRA, AccountType.HSA]:
            # Tax-deferred: reduce current taxable income
            tax_with = TaxCalculator.calculate_federal_income_tax(ordinary_income, filing_jointly)
            tax_without = TaxCalculator.calculate_federal_income_tax(ordinary_income - amount, filing_jointly)
            return tax_with - tax_without
        
        # Roth and taxable: no immediate tax benefit
        return 0.0



