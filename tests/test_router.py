import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.router import AgentRouter

def test_router():
    router = AgentRouter()

    print("\n" + "="*50)
    print("Test 1: Simple Query (No Memory)")
    print("="*50)
    msg1 = "Hello, what can you do for me?"
    print(f"User Message : {msg1}")
    res1 = router.route_query(msg1)
    for i, dec in enumerate(res1["route_decisions"]):
        print(f"\n--- Decision {i+1} ---")
        print(f"Route           : {dec['route']}")
        print(f"Rewritten Query : {dec['rewritten_query']}")
        print(f"Reasoning       : {dec['reasoning']}")

    print("\n" + "="*50)
    print("Test 2: Multi-Route Fan-Out Query")
    print("="*50)
    msg2 = "Please analyze my cashflow and also give me an update on the CSE market."
    print(f"User Message : {msg2}")
    res2 = router.route_query(msg2)
    for i, dec in enumerate(res2["route_decisions"]):
        print(f"\n--- Decision {i+1} ---")
        print(f"Route           : {dec['route']}")
        print(f"Rewritten Query : {dec['rewritten_query']}")
        print(f"Reasoning       : {dec['reasoning']}")

    print("\n" + "="*50)
    print("Test 3: Query Reformulation (Pronoun Resolution using Memory)")
    print("="*50)
    memory_context = "### Recent Conversation:\nUser: I am planning to buy 100 shares of JKH on the CSE tomorrow.\nAssistant: That sounds like a solid long-term investment. Let me know if you need any further analysis on JKH."
    msg3 = "Actually, let's cancel that plan."
    print(f"Memory Context :\n{memory_context}")
    print(f"\nUser Message   : {msg3}")
    res3 = router.route_query(msg3, memory_context)
    for i, dec in enumerate(res3["route_decisions"]):
        print(f"\n--- Decision {i+1} ---")
        print(f"Route           : {dec['route']}")
        print(f"Rewritten Query : {dec['rewritten_query']}")
        print(f"Reasoning       : {dec['reasoning']}")
        
    print("\n" + "="*50)
    print("Test 4: Cashflow / RAG mix")
    print("="*50)
    msg4 = "Can you look at my uploaded PDF invoice and predict if I'll run out of cash this month?"
    print(f"User Message : {msg4}")
    res4 = router.route_query(msg4)
    for i, dec in enumerate(res4["route_decisions"]):
        print(f"\n--- Decision {i+1} ---")
        print(f"Route           : {dec['route']}")
        print(f"Rewritten Query : {dec['rewritten_query']}")
        print(f"Reasoning       : {dec['reasoning']}")

if __name__ == "__main__":
    test_router()
