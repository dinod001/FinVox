import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.orchestrator import AgentOrchestrator

def test_orchestrator():
    orchestrator = AgentOrchestrator()
    
    user_id = "test_user_01"
    session_id = "test_session_01"
    
    print("\n" + "="*50)
    print("Orchestrator Test: Single Route")
    print("="*50)
    msg1 = "Hello FinVox, how are you today?"
    print(f"User: {msg1}")
    res1 = orchestrator.chat(msg1, user_id, session_id)
    print(f"\nRoutes Taken : {res1['routes']}")
    print(f"Agent Answer : {res1['answer']}")
    print(f"Latency      : {res1['latency_ms']} ms")
    
    print("\n" + "="*50)
    print("Orchestrator Test: Multi-Route Fan-Out")
    print("="*50)
    msg2 = "Please analyze my cashflow and tell me the market status of CSE."
    print(f"User: {msg2}")
    res2 = orchestrator.chat(msg2, user_id, session_id)
    print(f"\nRoutes Taken : {res2['routes']}")
    print(f"Tool Output  : {res2['tool_output']}")
    print(f"Agent Answer : {res2['answer']}")
    print(f"Latency      : {res2['latency_ms']} ms")

    print("\n" + "="*50)
    print("Orchestrator Test: RAG Tool (Document Analysis)")
    print("="*50)
    msg3 = "I just uploaded a PDF invoice. Can you analyze it and extract the total amount and due date?"
    print(f"User: {msg3}")
    res3 = orchestrator.chat(msg3, user_id, session_id)
    print(f"\nRoutes Taken : {res3['routes']}")
    print(f"Tool Output  : {res3['tool_output']}")
    print(f"Agent Answer : {res3['answer']}")
    print(f"Latency      : {res3['latency_ms']} ms")

    print("\n" + "="*50)
    print("Orchestrator Test: Investment Advisor")
    print("="*50)
    msg4 = "I have a surplus of 500,000 LKR this month in my SME account. What are some safe short-term investment options in Sri Lanka?"
    print(f"User: {msg4}")
    res4 = orchestrator.chat(msg4, user_id, session_id)
    print(f"\nRoutes Taken : {res4['routes']}")
    print(f"Agent Answer : {res4['answer']}")
    print(f"Latency      : {res4['latency_ms']} ms")

    print("\n" + "="*50)
    print("Orchestrator Test: Complex Multi-Route (RAG + Cashflow + Investment)")
    print("="*50)
    msg5 = "Look at the PDF invoice I uploaded. Based on the amount due, will I have enough cash flow to cover it next month? If I have a surplus, what should I invest in?"
    print(f"User: {msg5}")
    res5 = orchestrator.chat(msg5, user_id, session_id)
    print(f"\nRoutes Taken : {res5['routes']}")
    print(f"Tool Output  : {res5['tool_output']}")
    print(f"Agent Answer : {res5['answer']}")
    print(f"Latency      : {res5['latency_ms']} ms")

if __name__ == "__main__":
    test_orchestrator()
