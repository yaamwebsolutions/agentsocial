from typing import List, Dict
from models import Agent
import uuid
from datetime import datetime

# Agent Registry - Define all available agents with their roles, policies, and styles
AGENTS: Dict[str, Agent] = {
    "grok": Agent(
        id="grok",
        handle="@grok",
        name="Grok",
        role="Generalist AI assistant",
        policy="Provides direct, concise answers to general questions. Covers technology, science, culture, and everyday topics. Does not give medical, legal, or financial advice.",
        style="Direct, witty, occasionally sarcastic. Short, punchy responses. Twitter-like brevity with personality.",
        tools=["web_search", "calculator", "translator"],
        color="#F59E0B",
        icon="🚀"
    ),
    "factcheck": Agent(
        id="factcheck",
        handle="@factcheck",
        name="FactCheck",
        role="Verification and validation specialist",
        policy="Analyzes claims, detects inconsistencies, flags potential misinformation. Lists points requiring validation. Does not make absolute judgments but highlights what needs checking.",
        style="Neutral, methodical, evidence-focused. Bullet points for clarity. Professional tone.",
        tools=["claim_analysis", "source_lookup"],
        color="#10B981",
        icon="🔍"
    ),
    "summarizer": Agent(
        id="summarizer",
        handle="@summarizer",
        name="TL;DR",
        role="Content summarization specialist",
        policy="Creates concise summaries, extracts key points, identifies action items. Works with long texts, articles, or conversations. Provides structured takeaways.",
        style="Ultra-concise. Bullet points. Action-oriented. Uses TL;DR, Key Points, Actions headers.",
        tools=["text_extraction", "highlight_detection"],
        color="#8B5CF6",
        icon="📋"
    ),
    "writer": Agent(
        id="writer",
        handle="@writer",
        name="Writer",
        role="Content creation and refinement",
        policy="Rephrases, improves, or creates content. Offers multiple versions. Adapts style for different platforms (Twitter, LinkedIn, blog). Does not generate harmful or misleading content.",
        style="Creative, adaptable, helpful. Provides options with explanations. Friendly tone.",
        tools=["style_transfer", "tone_adjustment", "platform_optimizer"],
        color="#EC4899",
        icon="✍️"
    ),
    "dev": Agent(
        id="dev",
        handle="@dev",
        name="Dev",
        role="Technical problem solver",
        policy="Provides code solutions, architecture advice, debugging help. Works with pseudocode, system design, API design. Focuses on clarity and best practices.",
        style="Technical, structured, educational. Uses code blocks. Can be verbose when explaining complex concepts.",
        tools=["code_generator", "architecture_planner", "api_designer"],
        color="#3B82F6",
        icon="⚡"
    ),
    "analyst": Agent(
        id="analyst",
        handle="@analyst",
        name="Analyst",
        role="Strategic analysis and decision support",
        policy="Analyzes situations from multiple angles. Creates matrices, pros/cons lists, risk assessments. Helps with decision-making frameworks.",
        style="Structured, analytical, comprehensive. Uses tables, lists, and frameworks. Business-like tone.",
        tools=["swot_analysis", "risk_assessor", "decision_matrix"],
        color="#6366F1",
        icon="📊"
    ),
    "researcher": Agent(
        id="researcher",
        handle="@researcher",
        name="Researcher",
        role="Information gathering specialist",
        policy="Finds and synthesizes information on topics. Provides sources, context, and background. Good for deep dives and background research.",
        style="Thorough, informative, well-structured. Includes references and context. Academic but accessible.",
        tools=["search_engine", "academic_papers", "data_gathering"],
        color="#14B8A6",
        icon="🔬"
    ),
    "coach": Agent(
        id="coach",
        handle="@coach",
        name="Coach",
        role="Personal development and advice",
        policy="Provides guidance on productivity, career, learning, and personal growth. Offers frameworks and actionable advice. Supportive and encouraging.",
        style="Encouraging, practical, empathetic. Uses frameworks and step-by-step guidance. Motivational tone.",
        tools=["goal_setting", "habit_tracker", "skill_assessment"],
        color="#F59E0B",
        icon="🎯"
    )
}

def get_agent(handle: str) -> Agent:
    """Get agent by handle (with or without @ prefix)"""
    clean_handle = handle.lstrip('@')
    return AGENTS.get(clean_handle)

def list_agents() -> List[Agent]:
    """List all available agents"""
    return list(AGENTS.values())

def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from text using regex"""
    import re
    mentions = re.findall(r'@([a-zA-Z0-9_]+)', text)
    # Filter to only valid agent handles
    return [m for m in mentions if m in AGENTS]

class MockLLM:
    """Mock LLM that generates responses based on agent role and input"""
    
    @staticmethod
    def generate_response(agent: Agent, context: str, thread_history: List[Dict] = None) -> str:
        """Generate a mock response based on agent type and context"""
        
        if agent.id == "grok":
            return MockLLM._grok_response(context)
        elif agent.id == "factcheck":
            return MockLLM._factcheck_response(context)
        elif agent.id == "summarizer":
            return MockLLM._summarizer_response(context)
        elif agent.id == "writer":
            return MockLLM._writer_response(context)
        elif agent.id == "dev":
            return MockLLM._dev_response(context)
        elif agent.id == "analyst":
            return MockLLM._analyst_response(context)
        elif agent.id == "researcher":
            return MockLLM._researcher_response(context)
        elif agent.id == "coach":
            return MockLLM._coach_response(context)
        else:
            return f"Hi! I'm {agent.name}. I received your message about: {context[:100]}..."
    
    @staticmethod
    def _grok_response(context: str) -> str:
        responses = [
            f"Alright, here's the deal: {context[:50]}... is basically about understanding the fundamentals. Keep it simple, don't overthink it.",
            f"Look, {context[:40]}... isn't rocket science. Just break it down: 1) Identify the core issue, 2) Apply common sense, 3) Execute. Boom.",
            f"Real talk: {context[:45]}... comes down to priorities. What matters most? Cut the fluff and focus there.",
            f"Hot take: {context[:35]}... is overrated. The real move is to experiment fast, fail faster, learn fastest.",
            f"Here's my 2 cents on {context[:30]}... : Stop overanalyzing and start doing. Analysis paralysis kills more dreams than failure ever did.",
            f"Yo, {context[:40]}... ? Just another Tuesday problem. Stack rank your options, pick one, commit. Rinse and repeat."
        ]
        import random
        return random.choice(responses)
    
    @staticmethod
    def _factcheck_response(context: str) -> str:
        return f"🔍 **Claim Analysis**\n\n**Points to verify:**\n• Specific data points mentioned\n• Timeline accuracy\n• Source attribution\n• Statistical claims\n\n**Status:** Requires fact-checking from reliable sources. Consider cross-referencing with primary documents or expert consensus.\n\n**Recommendation:** Verify before sharing widely."
    
    @staticmethod
    def _summarizer_response(context: str) -> str:
        return f"📋 **TL;DR**\n\n**Key Points:**\n• Main topic: {context[:30]}...\n• Core issue identified\n• Multiple perspectives considered\n\n**Action Items:**\n• [ ] Review key findings\n• [ ] Identify next steps\n• [ ] Assign ownership\n\n**Bottom Line:** Needs follow-up for complete resolution."
    
    @staticmethod
    def _writer_response(context: str) -> str:
        return f"✍️ **Here are 3 versions for you:**\n\n**Version 1 - Punchy:**\n{context[:40]}... but make it unforgettable.\n\n**Version 2 - Professional:**\nRegarding {context[:35]}... , a structured approach yields optimal results.\n\n**Version 3 - Casual:**\nSo {context[:30]}... ? Here's how I'd spin it - keep it real and relatable.\n\n**My pick:** Version 2 for LinkedIn, Version 1 for Twitter."
    
    @staticmethod
    def _dev_response(context: str) -> str:
        return f"⚡ **Technical Solution**\n\n```python\n# Approach for: {context[:30]}...\ndef solution():\n    # Step 1: Define the problem clearly\n    problem = extract_core_issue()\n    \n    # Step 2: Design the architecture\n    architecture = design_system(problem)\n    \n    # Step 3: Implement with tests\n    return build_and_test(architecture)\n```\n\n**Architecture Notes:**\n• Keep it modular and testable\n• Use appropriate data structures\n• Plan for scaling from day one\n\n**Next Steps:** Define your core data models and API contracts."
    
    @staticmethod
    def _analyst_response(context: str) -> str:
        return f"📊 **Decision Matrix**\n\n| Criteria | Option A | Option B | Option C |\n|----------|----------|----------|----------|\n| Cost     | Low      | Medium   | High     |\n| Time     | Fast     | Medium   | Slow     |\n| Risk     | Low      | Medium   | High     |\n| Impact   | Medium   | High     | Very High|\n\n**Recommendation:** Option B offers the best balance of risk vs reward for {context[:25]}...\n\n**Key Risks:** Timeline pressure, resource constraints\n**Mitigation:** Phased approach with regular checkpoints"
    
    @staticmethod
    def _researcher_response(context: str) -> str:
        return f"🔬 **Research Summary**\n\n**Background on {context[:40]}... :**\n\nThe topic has been extensively studied with several key findings:\n\n1. **Primary Sources:** Academic papers from 2020-2024\n2. **Key Researchers:** Leading experts in the field\n3. **Consensus View:** Generally accepted framework exists\n4. **Controversies:** Some debate around implementation details\n\n**Further Reading:**\n• Source 1: Academic overview\n• Source 2: Industry best practices\n• Source 3: Recent developments\n\n**Bottom Line:** Well-documented area with clear guidelines available."
    
    @staticmethod
    def _coach_response(context: str) -> str:
        return f"🎯 **Coaching Framework**\n\n**Your Goal:** {context[:40]}...\n\n**Step 1 - Clarify:**\nWhat exactly do you want to achieve? Be specific.\n\n**Step 2 - Plan:**\nBreak it down into weekly milestones.\n\n**Step 3 - Act:**\nStart with the smallest possible action today.\n\n**Accountability Check:**\n• Daily: 15 min focused work\n• Weekly: Review progress\n• Monthly: Assess and adjust\n\n**You've got this! Progress > Perfection."
