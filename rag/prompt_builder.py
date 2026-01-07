"""
Prompt Builder
Constructs system and developer prompts for the BowlVision Coach LLM.
"""

import json
from pathlib import Path
from typing import Optional


def load_knowledge() -> dict:
    """Load the knowledge.json file."""
    knowledge_path = Path(__file__).parent / 'knowledge.json'
    with open(knowledge_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_system_prompt(knowledge: dict) -> str:
    """
    Build the system prompt with grounding rules.
    
    Args:
        knowledge: The knowledge.json data
        
    Returns:
        System prompt string
    """
    tone = knowledge.get('tone_and_style', {})
    grounding = knowledge.get('grounding_and_safety_rules', {})
    
    hard_rules = grounding.get('hard_grounding', [])
    must_include = grounding.get('response_contract', {}).get('must_include_when_possible', [])
    must_avoid = grounding.get('response_contract', {}).get('must_avoid', [])
    format_rules = tone.get('format_rules', [])
    
    return f"""You are the BowlVision Coach, an expert cricket bowling coach providing report-grounded coaching advice.

VOICE AND TONE:
{tone.get('voice', 'Direct, coach-like, simple language.')}

LENGTH TARGETS:
- Default responses: {tone.get('length_targets', {}).get('default', '6-14 bullets')}
- Deep dives (when asked): {tone.get('length_targets', {}).get('deep_dive', '300-500 words')}
- Drill descriptions: {tone.get('length_targets', {}).get('drills', '3-6 bullets per drill')}

HARD GROUNDING RULES (MUST FOLLOW):
{chr(10).join(f'- {rule}' for rule in hard_rules)}

FORMAT RULES:
{chr(10).join(f'- {rule}' for rule in format_rules)}

RESPONSE CONTRACT:
When possible, include:
{chr(10).join(f'- {item}' for item in must_include)}

Must avoid:
{chr(10).join(f'- {item}' for item in must_avoid)}

You will receive the bowler's report context pack and coaching knowledge. Stay grounded in this data. If something is not in the report, say so plainly."""


def build_developer_prompt() -> str:
    """Build the developer prompt with response structure."""
    return """RESPONSE STRUCTURE:
When providing coaching feedback, structure your response as follows:

1. **Strengths** - What the bowler is doing well (reference specific metrics/scores)
2. **Priority Fixes** - Top 1-3 areas to focus on (lowest scores or critical issues)
3. **Action Items** - Specific drills and cues
4. **Quick Verification** - How to self-check progress

Use bullet points. Be concise. Reference metric names and scores directly from the context pack.
When a metric score is 0-25: treat as urgent. 25-60: moderate priority. 60-85: refine. 85-100: maintain as strength.

For missing data, say "This metric was not computed" rather than guessing."""


def build_knowledge_summary(knowledge: dict) -> str:
    """
    Build a condensed summary of coaching knowledge for the LLM.
    
    Args:
        knowledge: The knowledge.json data
        
    Returns:
        Knowledge summary string
    """
    framework = knowledge.get('coaching_framework', {})
    rubrics = knowledge.get('rubrics', {})
    drills = knowledge.get('drill_library', {})
    
    # Prioritization rules
    priority_rules = framework.get('prioritization_rules', [])
    
    # Build metric rubrics summary
    metric_rubrics = []
    for metric_id, info in rubrics.get('metrics', {}).items():
        rubric = f"**{metric_id}**: {info.get('what_it_means', '')}"
        if info.get('fix_cues'):
            rubric += f"\n  Cues: {', '.join(info['fix_cues'][:2])}"
        if info.get('drills'):
            rubric += f"\n  Drills: {', '.join(info['drills'][:3])}"
        metric_rubrics.append(rubric)
    
    # Build drill library summary
    drill_summaries = []
    for drill_id, info in drills.items():
        drill_summaries.append(f"**{drill_id}**: {info.get('goal', '')}")
    
    return f"""COACHING KNOWLEDGE:

PRIORITIZATION:
{chr(10).join(f'- {rule}' for rule in priority_rules)}

METRIC RUBRICS:
{chr(10).join(metric_rubrics)}

AVAILABLE DRILLS:
{chr(10).join(drill_summaries)}"""


def build_context_prompt(context_pack: dict) -> str:
    """
    Build the context prompt containing the report data.
    
    Args:
        context_pack: The compact context pack from the report
        
    Returns:
        Context prompt string
    """
    return f"""CURRENT REPORT CONTEXT PACK:
```json
{json.dumps(context_pack, indent=2)}
```

Use ONLY the data above. Do not invent scores, angles, or frames not present in this context."""


def build_initial_message_prompt(context_pack: dict, knowledge: dict) -> str:
    """
    Build the prompt for generating the initial coach message.
    
    Args:
        context_pack: The compact context pack from the report
        knowledge: The knowledge.json data
        
    Returns:
        Initial message prompt
    """
    bowler_name = context_pack.get('bowler', {}).get('name', 'the bowler')
    
    return f"""Generate an initial coaching message for {bowler_name}.

Start with a brief greeting, then provide:
1. **Top Strengths** (2-3 bullets based on highest scores/best ratings)
2. **Priority Focus** (1-2 areas needing work based on lowest scores)
3. **Suggested First Drill** (one relevant drill from the knowledge base)

Keep it concise and actionable. End with an invitation to ask follow-up questions.
Reference actual metric names and scores from the context pack."""


def build_chat_messages(
    context_pack: dict,
    knowledge: dict,
    chat_history: list,
    user_message: str
) -> list:
    """
    Build the full message list for a chat request.
    
    Args:
        context_pack: The compact context pack from the report
        knowledge: The knowledge.json data
        chat_history: List of previous messages [{"role": "...", "content": "..."}]
        user_message: The new user message
        
    Returns:
        List of messages for the LLM
    """
    messages = [
        {"role": "system", "content": build_system_prompt(knowledge)},
        {"role": "user", "content": build_developer_prompt()},
        {"role": "user", "content": build_knowledge_summary(knowledge)},
        {"role": "user", "content": build_context_prompt(context_pack)},
    ]
    
    # Add chat history
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add new user message
    messages.append({"role": "user", "content": user_message})
    
    return messages


def build_initial_messages(context_pack: dict, knowledge: dict) -> list:
    """
    Build the message list for the initial coach message (no user input).
    
    Args:
        context_pack: The compact context pack from the report
        knowledge: The knowledge.json data
        
    Returns:
        List of messages for the LLM
    """
    messages = [
        {"role": "system", "content": build_system_prompt(knowledge)},
        {"role": "user", "content": build_developer_prompt()},
        {"role": "user", "content": build_knowledge_summary(knowledge)},
        {"role": "user", "content": build_context_prompt(context_pack)},
        {"role": "user", "content": build_initial_message_prompt(context_pack, knowledge)},
    ]
    
    return messages
