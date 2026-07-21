import os
import sys

# Ensure project root and src are in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from src.services.chat_service.crag_service import CRAGService
from src.services.chat_service.cag_service import CAGService
from src.services.chat_service.cag_cache import CAGCache
from src.services.chat_service.rag_service import QdrantRetriever
from src.infrastructure.llm.embeddings import get_embeddings
from src.infrastructure.llm.llm_provider import get_chat_llm

def test_cag():
    print("="*60)
    print("Integration Test: CAG + CRAG Service (Brain with Cache)")
    print("="*60)
    
    # 1. Initialize Components
    print("\nInitializing LLM and Embeddings...")
    embedder = get_embeddings()
    llm = get_chat_llm(temperature=0)
    
    print("Initializing Qdrant Retriever and Cache...")
    retriever = QdrantRetriever(
        embedder=embedder,
        top_k=4,
        score_threshold=0.5
    )
    
    print("Initializing CRAG and CAG Services...")
    crag_service = CRAGService(retriever=retriever, llm=llm)
    cag_cache = CAGCache(embedder=embedder)
    
    # Wrap CRAG with CAG
    cag_service = CAGService(crag_service=crag_service, cache=cag_cache)
    
    # 2. Define Test Cases (Questions and Expected Keywords)
    # The user fed data from a PDF (AXZIO AI B2B Strategy Report) and tables.
    test_cases = [
        {
            "question": "What is the main objective or strategy discussed in the AXZIO report?",
            "expected_keywords": ["AXZIO", "strategy", "B2B"]
        },
        {
            "question": "What is the primary objective of using LinkedIn according to the tactical execution plan?",
            "expected_keywords": ["Lead Generation", "Decision Makers"]
        },
        {
            "question": "Which platform should be used for Outbound Volume Pipelines?",
            "expected_keywords": ["Apollo", "Instantly"]
        },
        {
            "question": "How does AI impact the implementation plan?",
            "expected_keywords": ["implementation", "AI", "impact"]
        }
    ]
    
    print("\n--- Starting Tests ---")
    
    passed_count = 0
    for i, tc in enumerate(test_cases, 1):
        question = tc["question"]
        expected = tc["expected_keywords"]
        
        print(f"\nTest {i}: {question}")
        
        try:
            result = cag_service.generate(query=question)
            answer = result.get("answer", "")
            confidence = result.get("confidence_final", 0)
            correction_applied = result.get("correction_applied", False)
            cache_hit = result.get("cache_hit", False)
            
            print(f"Cache Hit: {cache_hit} | Confidence: {confidence:.2f} | Corrected: {correction_applied}")
            print(f"Answer: {answer[:200]}...")
            
            # Check if at least one expected keyword is in the answer
            answer_lower = answer.lower()
            matched_keywords = [kw for kw in expected if kw.lower() in answer_lower]
            
            if matched_keywords:
                print(f"Result: Passed ✅ (Found: {', '.join(matched_keywords)})")
                passed_count += 1
            else:
                print(f"Result: Failed ❌ (Expected to find some of: {', '.join(expected)})")
                
        except Exception as e:
            print(f"Result: Error ❌ ({str(e)})")
            
    print("="*60)
    print(f"Test Summary: {passed_count}/{len(test_cases)} Passed.")
    print("="*60)

if __name__ == "__main__":
    test_cag()
