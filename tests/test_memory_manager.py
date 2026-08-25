import time
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.memory.memory_manager import MemoryManager

def test_memory_flow():
    user_id = "user_test_123"
    session_id = "sess_456"

    manager = MemoryManager()

    print("\n--- Test 1: User Message Processing (Short-Term + Long-Term Check) ---")
    message_1 = "My monthly salary is 200,000 LKR"
    manager.process_user_message(user_id, session_id, message_1)
    
    manager.save_assistant_message(user_id, session_id, "Noted, I have saved your salary.")
    print("Messages saved.")
    
    # Wait a bit so we can clearly see the distinct operation if needed (though not strictly necessary)
    time.sleep(2)

    print("\n--- Test 2: User Message Processing (Update Fact via Vector Similarity) ---")
    message_2 = "Hey, I got a promotion! update my new monthly salary is 300,000 LKR"
    manager.process_user_message(user_id, session_id, message_2)

    print("\n--- Test 4: Querying final state ---")
    facts = manager.lt_store.query(user_id, "What is my salary?", k=3, threshold=0.0)
    print("Facts currently in Long Term Memory:")
    for f in facts:
        print(f" - [{f.id}] {f.text} (Score: {f.score})")

if __name__ == "__main__":
    test_memory_flow()
