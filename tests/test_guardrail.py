import os
import sys

# Ensure FinVox is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.guardrail import check_guardrail
from colorama import init, Fore

init(autoreset=True)

def run_tests():
    print("=" * 60)
    print("  Guardrail Tests")
    print("=" * 60)
    
    test_cases = [
        # In-Scope expected
        ("How much did we spend on marketing last month?", True),
        ("Should I invest in CSE or keep it in FD?", True),
        ("Wait a second let me check the invoice.", True),
        ("Yes, proceed with the extraction.", True),
        ("What's our net payable for Q2?", True),
        
        # Out-of-Scope expected
        ("Who won the cricket match yesterday?", False),
        ("Write a python script to sort a list.", False),
        ("I have a stomach ache, what should I take?", False),
        ("What's the capital of Japan?", False),
        ("tell me a joke", False)
    ]
    
    passed = 0
    
    for query, expected in test_cases:
        result = check_guardrail(query)
        
        if result == expected:
            passed += 1
            status = Fore.GREEN + "PASS" + Fore.RESET
        else:
            status = Fore.RED + "FAIL" + Fore.RESET
            
        print(f"[{status}] Query: '{query}'")
        print(f"       Expected: {expected}, Got: {result}\n")
        
    print("=" * 60)
    print(f"  Passed {passed} / {len(test_cases)} tests.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
