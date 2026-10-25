from calculator import calculate_profit
from evaluator import is_profitable

def analyze_cost(price,cost):
    profit=calculate_profit(price,cost)
    return{"profit":profit,
        "is_profitable":is_profitable}