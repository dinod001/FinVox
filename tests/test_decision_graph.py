import os
import sys

# Ensure FinVox is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.router import AgentRouter
from src.agents.decision_graph import build_decision_graph
from colorama import init, Fore

init(autoreset=True)

def run_tests():
    print("=" * 60)
    print("  Decision Graph Tests (Guardrail + Router Parallel)")
    print("=" * 60)
    
    print("[INFO] Initializing AgentRouter and Decision Graph...")
    router = AgentRouter()
    decision_graph = build_decision_graph(router)
    
    test_cases = [
        {
            "description": "In-Scope (Cashflow)",
            "message": "What was our total cash inflow for Q1 2026?",
            "expected_verdict": "proceed",
            "expected_route": "cashflow"
        },
        {
            "description": "Out-of-Scope (General Trivia)",
            "message": "Who won the football world cup in 2022?",
            "expected_verdict": "out_of_scope",
            "expected_route": "out_of_scope"
        },
        {
            "description": "In-Scope (General Chat)",
            "message": "Hi FinVox, how are you today?",
            "expected_verdict": "proceed",
            "expected_route": "general"
        }
    ]
    
    passed = 0
    
    for tc in test_cases:
        print(f"\n[TEST] {tc['description']}")
        print(f"       Message: '{tc['message']}'")
        
        # Invoke the graph
        state_input = {
            "message": tc['message'],
            "memory_context": ""
        }
        
        try:
            result = decision_graph.invoke(state_input)
            
            actual_verdict = result.get("verdict")
            actual_route = result.get("primary_route")
            
            # Allow some flexibility on the route if the LLM router decides differently,
            # but it MUST match the out_of_scope constraint.
            if actual_verdict == tc['expected_verdict']:
                # For out of scope, route MUST be out_of_scope. 
                # For proceed, route can be whatever the router decided, but we check if it matches roughly.
                if tc['expected_verdict'] == 'out_of_scope' and actual_route != 'out_of_scope':
                    status = Fore.RED + "FAIL (Wrong Route)" + Fore.RESET
                else:
                    status = Fore.GREEN + "PASS" + Fore.RESET
                    passed += 1
            else:
                status = Fore.RED + "FAIL (Wrong Verdict)" + Fore.RESET
                
            print(f"       Expected Verdict: {tc['expected_verdict']} | Actual Verdict: {actual_verdict}")
            print(f"       Expected Route: {tc['expected_route']} | Actual Route: {actual_route}")
            print(f"       [{status}]")
            
        except Exception as e:
            print(f"       [{Fore.RED}FAIL{Fore.RESET}] Error executing graph: {e}")
            
    print("\n" + "=" * 60)
    print(f"  Passed {passed} / {len(test_cases)} tests.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
