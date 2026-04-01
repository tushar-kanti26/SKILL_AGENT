import re
from typing import TypedDict

from langgraph.graph import END, StateGraph

REQUIRED_FIELDS = [
    "target_skill",
    "current_level",
    "weekly_hours",
    "timeline_weeks",
    "goal",
]

BROAD_SKILL_HINTS = {
    "web technology": "Do you mean frontend development, backend development, or full-stack web development?",
    "web development": "Do you mean frontend development, backend development, or full-stack web development?",
    "frontend": "Do you want frontend development specifically, or should I build a broader web-development plan?",
    "backend": "Do you want backend development specifically, or should I build a broader web-development plan?",
    "full stack": "Do you want full-stack web development, or would you like me to focus on frontend or backend first?",
    "full-stack": "Do you want full-stack web development, or would you like me to focus on frontend or backend first?",
}


class AgentState(TypedDict):
    user_message: str
    profile: dict
    assistant_message: str
    ready_for_plan: bool


def _extract_profile_updates(user_message: str) -> dict:
    text = user_message.lower().strip()
    updates = {}

    level_values = ["beginner", "intermediate", "advanced"]
    for level in level_values:
        if level in text:
            updates["current_level"] = level
            break

    skill_patterns = [
        r"(?:i\s+want\s+to\s+learn|learn|study|master|explore)\s+(.+)$",
        r"(?:skill|topic|subject)\s*:\s*(.+)$",
    ]

    for pattern in skill_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            maybe_skill = match.group(1).strip().rstrip(".?!")
            maybe_skill = re.sub(r"\b(beginner|intermediate|advanced)\b.*$", "", maybe_skill).strip()
            if maybe_skill:
                updates["target_skill"] = maybe_skill
                break

    if not updates.get("target_skill"):
        normalized = re.sub(r"\s+", " ", text).strip()
        if normalized in {"frontend", "backend", "full stack", "full-stack"}:
            updates["target_skill"] = normalized.replace("full stack", "full-stack")

    tokens = text.replace(",", " ").split()
    for i, token in enumerate(tokens):
        if token.isdigit():
            num = int(token)
            if i + 1 < len(tokens) and tokens[i + 1].startswith("hour"):
                updates["weekly_hours"] = num
            elif i + 1 < len(tokens) and tokens[i + 1].startswith("week"):
                updates["timeline_weeks"] = num

    if "goal" in text and ":" in user_message:
        updates["goal"] = user_message.split(":", 1)[1].strip()

    return updates


def collect_profile(state: AgentState) -> AgentState:
    profile = dict(state.get("profile", {}))
    updates = _extract_profile_updates(state["user_message"])

    skill_hint = updates.get("target_skill")
    if skill_hint:
        normalized_hint = skill_hint.lower().strip()
        if normalized_hint in BROAD_SKILL_HINTS:
            assistant_message = BROAD_SKILL_HINTS[normalized_hint]
            profile["target_skill"] = None
            return {
                "user_message": state["user_message"],
                "profile": profile,
                "assistant_message": assistant_message,
                "ready_for_plan": False,
            }

    profile.update(updates)

    missing = [field for field in REQUIRED_FIELDS if not profile.get(field)]
    if missing:
        next_field = missing[0]
        prompts = {
            "target_skill": "Which skill do you want to learn? (example: Python, Data Science, React)",
            "current_level": "What is your current level? (beginner/intermediate/advanced)",
            "weekly_hours": "How many hours per week can you commit?",
            "timeline_weeks": "How many weeks is your target timeline?",
            "goal": "What is your main goal for learning this skill?",
        }
        assistant_message = prompts[next_field]
        ready_for_plan = False
    else:
        assistant_message = (
            "Perfect. I have enough information to generate your skill tree, "
            "weekly timetable, and recommended resources."
        )
        ready_for_plan = True

    return {
        "user_message": state["user_message"],
        "profile": profile,
        "assistant_message": assistant_message,
        "ready_for_plan": ready_for_plan,
    }


def route_next_step(state: AgentState):
    return END


def build_learning_agent():
    graph = StateGraph(AgentState)
    graph.add_node("collect_profile", collect_profile)
    graph.set_entry_point("collect_profile")
    graph.add_conditional_edges("collect_profile", route_next_step)
    return graph.compile()


learning_agent = build_learning_agent()
