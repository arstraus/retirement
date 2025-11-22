"""
Tax calculation module for retirement forecasting.
Includes federal, state, and capital gains tax calculations.
"""

from typing import Tuple


class TaxCalculator:
    """Calculate federal and state taxes for income and capital gains."""
    
    # 2024 Federal Tax Brackets (Single)
    FEDERAL_BRACKETS_SINGLE = [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float('inf'), 0.37)
    ]
    
    # 2024 Federal Tax Brackets (Married Filing Jointly)
    FEDERAL_BRACKETS_JOINT = [
        (23200, 0.10),
        (94300, 0.12),
        (201050, 0.22),
        (383900, 0.24),
        (487450, 0.32),
        (731200, 0.35),
        (float('inf'), 0.37)
    ]
    
    # 2024 Long-term Capital Gains Brackets (Married Filing Jointly)
    CAPITAL_GAINS_BRACKETS_JOINT = [
        (94050, 0.0),
        (583750, 0.15),
        (float('inf'), 0.20)
    ]
    
    # 2024 Long-term Capital Gains Brackets (Single)
    CAPITAL_GAINS_BRACKETS_SINGLE = [
        (47025, 0.0),
        (518900, 0.15),
        (float('inf'), 0.20)
    ]
    
    # Standard deductions for 2024
    STANDARD_DEDUCTION_SINGLE = 14600
    STANDARD_DEDUCTION_JOINT = 29200
    
    # State tax rates (flat rates for simplicity, can be expanded)
    STATE_TAX_RATES = {
        'California': 0.093,
        'New York': 0.0685,
        'Texas': 0.0,
        'Florida': 0.0,
        'Illinois': 0.0495,
        'Massachusetts': 0.05,
        'Washington': 0.0,
        'Colorado': 0.044,
        'Oregon': 0.099,
        'New Jersey': 0.0637,
        'None': 0.0
    }
    
    @staticmethod
    def calculate_federal_income_tax(income: float, filing_jointly: bool = False) -> float:
        """
        Calculate federal income tax using progressive brackets.
        
        Args:
            income: Gross income
            filing_jointly: Whether filing jointly (vs single)
            
        Returns:
            Federal income tax amount
        """
        brackets = TaxCalculator.FEDERAL_BRACKETS_JOINT if filing_jointly else TaxCalculator.FEDERAL_BRACKETS_SINGLE
        standard_deduction = TaxCalculator.STANDARD_DEDUCTION_JOINT if filing_jointly else TaxCalculator.STANDARD_DEDUCTION_SINGLE
        
        taxable_income = max(0, income - standard_deduction)
        
        if taxable_income <= 0:
            return 0.0
        
        tax = 0.0
        previous_bracket = 0.0
        
        for bracket_limit, rate in brackets:
            if taxable_income <= bracket_limit:
                tax += (taxable_income - previous_bracket) * rate
                break
            else:
                tax += (bracket_limit - previous_bracket) * rate
                previous_bracket = bracket_limit
        
        return tax
    
    @staticmethod
    def calculate_capital_gains_tax(gains: float, ordinary_income: float, filing_jointly: bool = False) -> float:
        """
        Calculate long-term capital gains tax.
        
        Args:
            gains: Capital gains amount
            ordinary_income: Ordinary income (affects capital gains brackets)
            filing_jointly: Whether filing jointly
            
        Returns:
            Capital gains tax amount
        """
        if gains <= 0:
            return 0.0
        
        brackets = TaxCalculator.CAPITAL_GAINS_BRACKETS_JOINT if filing_jointly else TaxCalculator.CAPITAL_GAINS_BRACKETS_SINGLE
        standard_deduction = TaxCalculator.STANDARD_DEDUCTION_JOINT if filing_jointly else TaxCalculator.STANDARD_DEDUCTION_SINGLE
        
        # Capital gains are taxed based on total income
        taxable_ordinary_income = max(0, ordinary_income - standard_deduction)
        
        tax = 0.0
        remaining_gains = gains
        previous_bracket = 0.0
        
        for bracket_limit, rate in brackets:
            # Determine how much room is left in this bracket
            bracket_top = bracket_limit
            bracket_bottom = max(previous_bracket, taxable_ordinary_income)
            
            if bracket_bottom >= bracket_top:
                previous_bracket = bracket_limit
                continue
            
            # Amount of gains that fit in this bracket
            gains_in_bracket = min(remaining_gains, bracket_top - bracket_bottom)
            
            if gains_in_bracket > 0:
                tax += gains_in_bracket * rate
                remaining_gains -= gains_in_bracket
                taxable_ordinary_income += gains_in_bracket
            
            previous_bracket = bracket_limit
            
            if remaining_gains <= 0:
                break
        
        return tax
    
    @staticmethod
    def calculate_state_tax(income: float, state: str) -> float:
        """
        Calculate state income tax.
        
        Args:
            income: Gross income
            state: State name
            
        Returns:
            State income tax amount
        """
        rate = TaxCalculator.STATE_TAX_RATES.get(state, 0.0)
        return income * rate
    
    @staticmethod
    def calculate_fica_tax(income: float, age: int) -> float:
        """
        Calculate FICA taxes (Social Security + Medicare).
        
        Args:
            income: Earned income
            age: Person's age (FICA doesn't apply after retirement typically)
            
        Returns:
            FICA tax amount
        """
        # Social Security: 6.2% up to wage base ($168,600 for 2024)
        # Medicare: 1.45% on all income, plus 0.9% on income over $200k
        
        ss_wage_base = 168600
        ss_rate = 0.062
        medicare_rate = 0.0145
        additional_medicare_threshold = 200000
        additional_medicare_rate = 0.009
        
        ss_tax = min(income, ss_wage_base) * ss_rate
        medicare_tax = income * medicare_rate
        
        if income > additional_medicare_threshold:
            medicare_tax += (income - additional_medicare_threshold) * additional_medicare_rate
        
        return ss_tax + medicare_tax
    
    @staticmethod
    def calculate_total_tax(
        ordinary_income: float,
        capital_gains: float,
        state: str,
        filing_jointly: bool = False,
        age: int = 30,
        is_working: bool = True
    ) -> Tuple[float, dict]:
        """
        Calculate total tax liability with breakdown.
        
        Args:
            ordinary_income: Ordinary income (wages, etc.)
            capital_gains: Long-term capital gains
            state: State name
            filing_jointly: Whether filing jointly
            age: Person's age
            is_working: Whether person is working (affects FICA)
            
        Returns:
            Tuple of (total_tax, tax_breakdown_dict)
        """
        federal_income_tax = TaxCalculator.calculate_federal_income_tax(ordinary_income, filing_jointly)
        capital_gains_tax = TaxCalculator.calculate_capital_gains_tax(capital_gains, ordinary_income, filing_jointly)
        state_tax = TaxCalculator.calculate_state_tax(ordinary_income + capital_gains, state)
        fica_tax = TaxCalculator.calculate_fica_tax(ordinary_income, age) if is_working else 0.0
        
        total_tax = federal_income_tax + capital_gains_tax + state_tax + fica_tax
        
        breakdown = {
            'federal_income': federal_income_tax,
            'capital_gains': capital_gains_tax,
            'state': state_tax,
            'fica': fica_tax,
            'total': total_tax
        }
        
        return total_tax, breakdown



