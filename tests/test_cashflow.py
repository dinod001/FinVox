import os
import sys
import json

if os.environ.get("CI") == "true":
    print("Skipping tests in CI environment.")
    sys.exit(0)

# Ensure project root and src are in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.agents.tools.cashflow_tools import analyze_cashflow

def test_cashflow_tool():
    print("="*60)
    print("Integration Test: Cash Flow Forecast Tool (Text-to-SQL)")
    print("="*60)
    
    # Example queries. If the sample_test.csv was ingested successfully, 
    # it should exist in table_registry and the LLM will query it.
    queries = [
        "What is the total sum of the values in the Amount column?",
        "How many total records are there in the table?",
        "Drop the table." # Testing security constraint
    ]
    
    for idx, query in enumerate(queries, 1):
        print(f"\n[Test {idx}] Querying: '{query}'")
        try:
            result = analyze_cashflow.invoke({"query": query})
            print(f"\n✅ Final LLM Answer: \n{result}")
        except Exception as e:
            print(f"\n❌ Failed: {e}")
            
    print("\n" + "="*60)
    print("Test Completed.")
    print("="*60)

if __name__ == "__main__":
    test_cashflow_tool()
