"""
Coach Service
Handles coach chat requests and responses.
"""

import logging
from typing import Optional

from rag.context_pack import get_context_pack, load_report
from rag.prompt_builder import (
    load_knowledge,
    build_initial_messages,
    build_chat_messages
)
from rag.adapters import gemini

# Set up logging
logger = logging.getLogger(__name__)


class CoachService:
    """Service for handling coach chat interactions."""
    
    def __init__(self, session_dir: str = 'data/run'):
        """
        Initialize the coach service.
        
        Args:
            session_dir: Path to the session directory
        """
        self.session_dir = session_dir
        self._context_pack = None
        self._knowledge = None
        self._report = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Load report and knowledge data.
        
        Returns:
            True if initialization successful, False otherwise
        """
        logger.info("Coach: Initializing...")
        
        # Load report
        self._report = load_report(self.session_dir)
        if self._report is None:
            logger.error("Coach: Failed to load report")
            return False
        
        # Build context pack
        logger.info("Coach: Building context pack...")
        self._context_pack = get_context_pack(self.session_dir)
        if self._context_pack is None:
            logger.error("Coach: Failed to build context pack")
            return False
        
        # Load knowledge
        logger.info("Coach: Loading knowledge base...")
        try:
            self._knowledge = load_knowledge()
        except Exception as e:
            logger.error(f"Coach: Failed to load knowledge: {e}")
            return False
        
        self._initialized = True
        logger.info("Coach: Initialization complete")
        return True
    
    @property
    def is_available(self) -> bool:
        """Check if the coach service is available."""
        return self._initialized and self._context_pack is not None
    
    @property
    def context_pack(self) -> Optional[dict]:
        """Get the current context pack."""
        return self._context_pack
    
    @property
    def knowledge(self) -> Optional[dict]:
        """Get the knowledge data."""
        return self._knowledge
    
    def get_initial_message(self) -> dict:
        """
        Generate the initial coach message (no user input needed).
        
        Returns:
            Dict with 'ok', 'message', and 'history' keys
        """
        if not self.is_available:
            return {
                'ok': False,
                'message': 'Coach service not available. Report may be missing.',
                'history': []
            }
        
        logger.info("Coach: Generating initial message...")
        
        try:
            # Configure Gemini if needed
            if not gemini.is_configured():
                gemini.configure()
            
            # Build messages for initial greeting
            messages = build_initial_messages(self._context_pack, self._knowledge)
            
            logger.info("Coach: Sending prompt to LLM...")
            response = gemini.chat_completion(messages)
            
            logger.info("Coach: Received response")
            
            # Return with initial history
            history = [{"role": "assistant", "content": response}]
            
            return {
                'ok': True,
                'message': response,
                'history': history
            }
        
        except Exception as e:
            logger.error(f"Coach: Error generating initial message: {e}")
            return {
                'ok': False,
                'message': f'Error connecting to coach: {str(e)}',
                'history': []
            }
    
    def chat(self, user_message: str, history: list) -> dict:
        """
        Handle a chat message from the user.
        
        Args:
            user_message: The user's message
            history: The current chat history
            
        Returns:
            Dict with 'ok', 'message', and 'history' keys
        """
        if not self.is_available:
            return {
                'ok': False,
                'message': 'Coach service not available. Report may be missing.',
                'history': history
            }
        
        logger.info(f"Coach: Processing user message: {user_message[:50]}...")
        
        try:
            # Configure Gemini if needed
            if not gemini.is_configured():
                gemini.configure()
            
            # Build messages with history and new message
            messages = build_chat_messages(
                self._context_pack,
                self._knowledge,
                history,
                user_message
            )
            
            logger.info("Coach: Sending prompt to LLM...")
            response = gemini.chat_completion(messages)
            
            logger.info("Coach: Received response")
            
            # Update history
            new_history = history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response}
            ]
            
            return {
                'ok': True,
                'message': response,
                'history': new_history
            }
        
        except Exception as e:
            logger.error(f"Coach: Error processing chat: {e}")
            return {
                'ok': False,
                'message': f'Error from coach: {str(e)}',
                'history': history
            }


# Global service instance
_coach_service: Optional[CoachService] = None


def get_coach_service(session_dir: str = 'data/run') -> CoachService:
    """
    Get or create the coach service singleton.
    
    Args:
        session_dir: Path to the session directory
        
    Returns:
        The CoachService instance
    """
    global _coach_service
    
    if _coach_service is None:
        _coach_service = CoachService(session_dir)
        _coach_service.initialize()
    
    return _coach_service


def reset_coach_service():
    """Reset the coach service (for re-initialization)."""
    global _coach_service
    _coach_service = None
