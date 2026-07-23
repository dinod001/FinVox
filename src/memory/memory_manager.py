import time
import uuid
from typing import List

from src.infrastructure.log import log
from src.infrastructure.config import ST_TTL_SECONDS, ST_MAX_TURNS

from src.memory.schemas import ConversationTurn, MemoryFact
from src.memory.short_term import PostgresShortTermStore
from src.memory.long_term import PostgresLongTermStore

class MemoryManager:
    """
    Orchestrates the AI memory subsystem.
    Handles Short-Term memory appending and Long-Term memory distillation.
    """

    def __init__(self):
        self.st_store = PostgresShortTermStore()
        self.lt_store = PostgresLongTermStore()

    def process_user_message(self, user_id: str, session_id: str, content: str) -> None:
        """
        Handles memory processing for an incoming user message.
        1. Always saves to Short-Term Memory.
        2. Optionally saves to Long-Term Memory (if keywords are triggered).
        """
        # 1. Save to Short-Term Memory
        turn = ConversationTurn(
            user_id=user_id,
            session_id=session_id,
            role="user",
            content=content,
            ts=time.time()
        )
        self.st_store.append(
            turn=turn,
            max_turns=ST_MAX_TURNS,
            ttl_seconds=ST_TTL_SECONDS
        )
        log.info(f"Saved short-term turn for user {user_id}, session {session_id} [user]")

        # 2. Try to distill to Long-Term Memory
        self._distill_long_term_facts(user_id, content)

    def save_assistant_message(self, user_id: str, session_id: str, content: str) -> None:
        """Saves only the assistant's reply to short-term memory."""
        turn = ConversationTurn(
            user_id=user_id,
            session_id=session_id,
            role="assistant",
            content=content,
            ts=time.time()
        )
        self.st_store.append(
            turn=turn,
            max_turns=ST_MAX_TURNS,
            ttl_seconds=ST_TTL_SECONDS
        )
        log.info(f"Saved short-term turn for user {user_id}, session {session_id} [assistant]")

    def get_memory_context(self, user_id: str, session_id: str, query: str, k_st: int = 10, k_lt: int = 3, lt_threshold: float = 0.5) -> str:
        """
        Retrieves both Short-Term and Long-Term memory and formats it for the LLM context.
        Called before generating an answer for every query.
        """
        # 1. Retrieve relevant long-term facts
        lt_facts = self.lt_store.query(user_id=user_id, text_query=query, k=k_lt, threshold=lt_threshold)
        
        # 2. Retrieve recent short-term conversation
        st_turns = self.st_store.recent(user_id=user_id, session_id=session_id, k=k_st)

        # Format Context
        context_parts = []
        
        if lt_facts:
            facts_str = "\n".join([f"- {fact.text}" for fact in lt_facts])
            context_parts.append(f"### Long-Term Knowledge about User:\n{facts_str}")
            
        if st_turns:
            chat_str = "\n".join([f"{turn.role.capitalize()}: {turn.content}" for turn in st_turns])
            context_parts.append(f"### Recent Conversation:\n{chat_str}")
            
        if not context_parts:
            return "No prior memory context available."
            
        return "\n\n".join(context_parts)

    def _distill_long_term_facts(self, user_id: str, current_message: str) -> None:
        """
        Extracts new facts from the current message.
        Uses a Keyword Trigger: Only calls the LLM if specific memory-related keywords are found.
        Uses Vector-First Overwrite Logic for saving.
        """
        # 0. Keyword-based Trigger (Saves LLM tokens and time)
        current_lower = current_message.lower()
        keywords = ["remember", "from now on", "remind me", "always", "never", "my", "i have", "i am", "i own", "update"]
        
        has_keyword = any(kw in current_lower for kw in keywords)
        if not has_keyword:
            log.info("No memory keywords found in message. Skipping LLM extraction.")
            return

        # 1. No LLM Extraction: Directly save the raw message if it passed the keyword trigger
        extracted_texts = [current_message.strip()]
        log.info(f"Trigger matched. Directly saving raw message as fact: {extracted_texts}")

        # 2. Vector-First Overwrite Logic for each extracted fact
        for new_fact_text in extracted_texts:
            # Query existing facts with a very high similarity threshold (e.g. 90%)
            # This handles contradiction/update natively.
            similar_facts = self.lt_store.query(
                user_id=user_id,
                text_query=new_fact_text,
                k=1,
                threshold=0.90
            )

            if similar_facts:
                # Update (Overwrite) the existing fact
                existing_fact = similar_facts[0]
                log.info(f"High similarity match found! Updating existing fact [{existing_fact.id}] -> '{new_fact_text}'")
                
                updated_fact = MemoryFact(
                    id=existing_fact.id, # Keep same ID
                    user_id=user_id,
                    text=new_fact_text,  # New Text
                    score=existing_fact.score,
                    tags=existing_fact.tags,
                    created_at=existing_fact.created_at,
                    last_used_at=time.time(),
                    ttl_at=existing_fact.ttl_at,
                    pin=existing_fact.pin
                )
                self.lt_store.upsert([updated_fact])
            else:
                # Insert as a brand new fact
                new_id = f"fact_{uuid.uuid4().hex[:8]}"
                log.info(f"No match found. Inserting new fact [{new_id}] -> '{new_fact_text}'")
                
                new_fact = MemoryFact(
                    id=new_id,
                    user_id=user_id,
                    text=new_fact_text,
                    score=1.0,
                    tags=[],
                    created_at=time.time(),
                    last_used_at=time.time()
                )
                self.lt_store.upsert([new_fact])
