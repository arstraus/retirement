"""
Scenario management for saving and loading retirement forecasts.
"""

import json
from typing import Dict, List, Any
from datetime import datetime
from retirement_calculator import Person


class ScenarioManager:
    """Manage saving and loading retirement scenarios."""
    
    @staticmethod
    def save_scenario(
        scenario_name: str,
        people: List[Person],
        initial_assets: float,
        annual_expenses: float,
        expense_growth_rate: float,
        investment_return_rate: float,
        state: str,
        additional_contributions: float,
        social_security_age: int,
        social_security_benefit: float,
        inflation_rate: float,
        forecast_years: int,
        account_balances: Dict[str, float] = None,
        contribution_allocation: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Create a scenario dictionary that can be saved to JSON.
        
        Returns:
            Dictionary containing all scenario parameters
        """
        scenario = {
            "scenario_name": scenario_name,
            "created_date": datetime.now().isoformat(),
            "version": "2.1",
            "people": [
                {
                    "name": person.name,
                    "age": person.age,
                    "retirement_age": person.retirement_age,
                    "current_income": person.current_income,
                    "income_growth_rate": person.income_growth_rate,
                    "retirement_income": person.retirement_income,
                    "annual_rsu_vesting": person.annual_rsu_vesting
                }
                for person in people
            ],
            "financial": {
                "initial_assets": initial_assets,
                "annual_expenses": annual_expenses,
                "expense_growth_rate": expense_growth_rate,
                "additional_contributions": additional_contributions,
                "account_balances": account_balances,
                "contribution_allocation": contribution_allocation
            },
            "investment": {
                "investment_return_rate": investment_return_rate,
                "inflation_rate": inflation_rate
            },
            "taxes": {
                "state": state
            },
            "social_security": {
                "age": social_security_age,
                "benefit": social_security_benefit
            },
            "forecast": {
                "years": forecast_years
            }
        }
        
        return scenario
    
    @staticmethod
    def scenario_to_json(scenario: Dict[str, Any]) -> str:
        """
        Convert scenario dictionary to JSON string.
        
        Args:
            scenario: Scenario dictionary
            
        Returns:
            JSON string
        """
        return json.dumps(scenario, indent=2)
    
    @staticmethod
    def save_scenario_to_file(scenario: Dict[str, Any], filename: str) -> None:
        """
        Save scenario to a JSON file.
        
        Args:
            scenario: Scenario dictionary
            filename: Path to save file
        """
        with open(filename, 'w') as f:
            json.dump(scenario, f, indent=2)
    
    @staticmethod
    def load_scenario_from_json(json_str: str) -> Dict[str, Any]:
        """
        Load scenario from JSON string.
        
        Args:
            json_str: JSON string containing scenario
            
        Returns:
            Scenario dictionary
        """
        return json.loads(json_str)
    
    @staticmethod
    def load_scenario_from_file(filename: str) -> Dict[str, Any]:
        """
        Load scenario from a JSON file.
        
        Args:
            filename: Path to file
            
        Returns:
            Scenario dictionary
        """
        with open(filename, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def create_people_from_scenario(scenario: Dict[str, Any]) -> List[Person]:
        """
        Create Person objects from scenario data.
        
        Args:
            scenario: Scenario dictionary
            
        Returns:
            List of Person objects
        """
        people = []
        for person_data in scenario["people"]:
            person = Person(
                name=person_data["name"],
                age=person_data["age"],
                retirement_age=person_data["retirement_age"],
                current_income=person_data["current_income"],
                income_growth_rate=person_data["income_growth_rate"],
                retirement_income=person_data["retirement_income"],
                annual_rsu_vesting=person_data.get("annual_rsu_vesting", 0.0)
            )
            people.append(person)
        
        return people
    
    @staticmethod
    def get_scenario_summary(scenario: Dict[str, Any]) -> str:
        """
        Get a human-readable summary of a scenario.
        
        Args:
            scenario: Scenario dictionary
            
        Returns:
            Summary string
        """
        num_people = len(scenario["people"])
        total_income = sum(p["current_income"] + p.get("annual_rsu_vesting", 0) 
                          for p in scenario["people"])
        
        summary = f"""
Scenario: {scenario['scenario_name']}
Created: {scenario.get('created_date', 'Unknown')}

Household:
  People: {num_people}
  Total Income: ${total_income:,.0f}
  State: {scenario['taxes']['state']}

Financial:
  Starting Assets: ${scenario['financial']['initial_assets']:,.0f}
  Annual Expenses: ${scenario['financial']['annual_expenses']:,.0f}
  
Investment:
  Return Rate: {scenario['investment']['investment_return_rate']*100:.1f}%
  Inflation Rate: {scenario['investment']['inflation_rate']*100:.1f}%
"""
        return summary.strip()
    
    @staticmethod
    def compare_scenarios(scenario1: Dict[str, Any], scenario2: Dict[str, Any]) -> str:
        """
        Compare two scenarios and highlight differences.
        
        Args:
            scenario1: First scenario
            scenario2: Second scenario
            
        Returns:
            Comparison string
        """
        differences = []
        
        # Compare basic info
        if len(scenario1["people"]) != len(scenario2["people"]):
            differences.append(f"Number of people: {len(scenario1['people'])} vs {len(scenario2['people'])}")
        
        # Compare financial
        if scenario1["financial"]["initial_assets"] != scenario2["financial"]["initial_assets"]:
            diff = scenario2["financial"]["initial_assets"] - scenario1["financial"]["initial_assets"]
            differences.append(f"Initial assets: ${diff:+,.0f}")
        
        if scenario1["financial"]["annual_expenses"] != scenario2["financial"]["annual_expenses"]:
            diff = scenario2["financial"]["annual_expenses"] - scenario1["financial"]["annual_expenses"]
            differences.append(f"Annual expenses: ${diff:+,.0f}")
        
        # Compare investment rates
        if scenario1["investment"]["investment_return_rate"] != scenario2["investment"]["investment_return_rate"]:
            diff = (scenario2["investment"]["investment_return_rate"] - scenario1["investment"]["investment_return_rate"]) * 100
            differences.append(f"Investment return: {diff:+.1f}%")
        
        if not differences:
            return "Scenarios are identical"
        
        return "Differences:\n" + "\n".join(f"  • {d}" for d in differences)



