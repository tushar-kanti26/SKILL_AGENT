import json
from importlib import import_module
from collections import defaultdict

from app.core.config import settings


ALLOWED_RESOURCE_TYPES = {"youtube", "website", "book"}

SKILL_ROADMAPS = {
    "web technology": {
        "canonical_skill": "web development",
        "subskills": [
            "HTML fundamentals",
            "CSS layout and responsive design",
            "JavaScript basics and DOM",
            "Git and GitHub workflow",
            "Frontend framework basics",
            "API integration and deployment",
        ],
    },
    "web development": {
        "canonical_skill": "web development",
        "subskills": [
            "HTML fundamentals",
            "CSS layout and responsive design",
            "JavaScript basics and DOM",
            "Git and GitHub workflow",
            "Frontend framework basics",
            "API integration and deployment",
        ],
    },
    "frontend": {
        "canonical_skill": "frontend development",
        "subskills": [
            "HTML fundamentals",
            "CSS layout and responsive design",
            "JavaScript basics and DOM",
            "React or Vue fundamentals",
            "State management and forms",
            "Deployment and portfolio project",
        ],
    },
}


def _resource_pool(skill: str):
    # Curated starter resources per type. Extend this map for more skills.
    generic = {
        "youtube": [
            ("freeCodeCamp", "https://www.youtube.com/@freecodecamp"),
            ("Fireship", "https://www.youtube.com/@Fireship"),
            ("Traversy Media", "https://www.youtube.com/@TraversyMedia"),
        ],
        "website": [
            ("roadmap.sh", f"https://roadmap.sh/{skill.lower().replace(' ', '-') if skill else ''}"),
            ("MDN", "https://developer.mozilla.org/"),
            ("GeeksforGeeks", "https://www.geeksforgeeks.org/"),
        ],
        "book": [
            ("Atomic Habits", "https://jamesclear.com/atomic-habits"),
            ("Deep Work", "https://calnewport.com/writing/"),
            ("The Pragmatic Programmer", "https://pragprog.com/titles/tpp20/the-pragmatic-programmer-20th-anniversary-edition/"),
        ],
    }
    return generic


def _resolve_skill_profile(skill: str) -> dict:
    normalized = skill.lower().strip()
    for key, roadmap in SKILL_ROADMAPS.items():
        if key in normalized:
            return roadmap
    return {
        "canonical_skill": skill,
        "subskills": [
            f"Core concepts of {skill}",
            f"Practical exercises in {skill}",
            f"Build a project using {skill}",
            f"Review and portfolio work for {skill}",
        ],
    }


def _fallback_schedule(profile: dict) -> dict:
    skill = profile["target_skill"]
    level = profile["current_level"]
    weeks = int(profile["timeline_weeks"])
    weekly_hours = int(profile["weekly_hours"])
    roadmap = _resolve_skill_profile(skill)
    canonical_skill = roadmap["canonical_skill"]
    subskills = roadmap["subskills"]

    foundation_weeks = max(1, weeks // 3)
    project_weeks = max(1, weeks // 3)
    advanced_weeks = max(1, weeks - foundation_weeks - project_weeks)

    skill_tree = {
        "root_skill": canonical_skill,
        "current_level": level,
        "milestones": [
            {
                "name": "Foundation",
                "duration_weeks": foundation_weeks,
                "outcomes": [subskills[0], subskills[1] if len(subskills) > 1 else "Build core vocabulary and concepts"],
            },
            {
                "name": "Applied Practice",
                "duration_weeks": project_weeks,
                "outcomes": [subskills[2] if len(subskills) > 2 else f"Implement hands-on mini projects in {canonical_skill}", subskills[3] if len(subskills) > 3 else "Improve problem-solving speed"],
            },
            {
                "name": "Advanced + Portfolio",
                "duration_weeks": advanced_weeks,
                "outcomes": [subskills[4] if len(subskills) > 4 else "Build end-to-end capstone", subskills[5] if len(subskills) > 5 else "Prepare portfolio and revision notes"],
            },
        ],
    }

    resources = _resource_pool(skill)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    minutes_per_day = max(30, (weekly_hours * 60) // len(days))

    tasks = []
    milestone_ranges = [
        (1, foundation_weeks, "Foundation"),
        (foundation_weeks + 1, foundation_weeks + project_weeks, "Applied Practice"),
        (foundation_weeks + project_weeks + 1, weeks, "Advanced + Portfolio"),
    ]

    resource_cycle = ["youtube", "website", "book", "youtube", "website", "youtube"]
    weekly_buckets = defaultdict(list)

    for week in range(1, weeks + 1):
        stage = "Advanced + Portfolio"
        for start, end, name in milestone_ranges:
            if start <= week <= end:
                stage = name
                break

        for i, day in enumerate(days):
            rtype = resource_cycle[i % len(resource_cycle)]
            rtitle, rurl = resources[rtype][(week + i) % len(resources[rtype])]
            task_title = f"{stage}: {subskills[min(week - 1, len(subskills) - 1)]}" if subskills else f"{stage}: {canonical_skill} session"
            task = {
                "week_number": week,
                "day_label": day,
                "title": task_title,
                "resource_type": rtype,
                "resource_title": rtitle,
                "resource_url": rurl,
                "estimated_minutes": minutes_per_day,
            }
            tasks.append(task)
            weekly_buckets[week].append(task)

    return {
        "skill_tree": skill_tree,
        "tasks": tasks,
        "weekly_overview": dict(weekly_buckets),
        "generation_mode": "fallback",
    }


def _normalize_generated_plan(profile: dict, generated: dict) -> dict:
    weeks = int(profile["timeline_weeks"])
    weekly_hours = int(profile["weekly_hours"])
    max_minutes = max(30, int((weekly_hours * 60) / 2))

    skill_profile = _resolve_skill_profile(profile["target_skill"])
    canonical_skill = skill_profile["canonical_skill"]

    skill_tree = generated.get("skill_tree") or {
        "root_skill": canonical_skill,
        "current_level": profile["current_level"],
        "milestones": [],
    }

    tasks = []
    for item in generated.get("tasks", []):
        try:
            week = int(item.get("week_number", 1))
        except Exception:
            week = 1
        week = max(1, min(week, weeks))

        rtype = str(item.get("resource_type", "website")).lower().strip()
        if rtype not in ALLOWED_RESOURCE_TYPES:
            rtype = "website"

        minutes = item.get("estimated_minutes", 60)
        try:
            minutes = int(minutes)
        except Exception:
            minutes = 60
        minutes = max(20, min(minutes, max_minutes))

        task = {
            "week_number": week,
            "day_label": str(item.get("day_label", "Mon"))[:20],
            "title": str(item.get("title", "Learning session"))[:250],
            "resource_type": rtype,
            "resource_title": str(item.get("resource_title", "Learning resource"))[:250],
            "resource_url": str(item.get("resource_url", "https://roadmap.sh/"))[:2000],
            "estimated_minutes": minutes,
        }
        tasks.append(task)

    if not tasks:
        return _fallback_schedule(profile)

    weekly_buckets = defaultdict(list)
    for task in tasks:
        weekly_buckets[task["week_number"]].append(task)

    return {
        "skill_tree": skill_tree,
        "tasks": tasks,
        "weekly_overview": dict(weekly_buckets),
        "generation_mode": "llm",
    }


def _llm_schedule(profile: dict) -> dict | None:
    if not settings.google_api_key:
        return None

    try:
        chat_google_module = import_module("langchain_google_genai")
        chat_google_class = getattr(chat_google_module, "ChatGoogleGenerativeAI")
    except Exception:
        return None

    model = chat_google_class(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0.2,
    )

    prompt = (
        "You are a learning coach. Return ONLY valid JSON with two keys: "
        "skill_tree and tasks. The tasks list must contain daily tasks with keys: "
        "week_number, day_label, title, resource_type (youtube|website|book), "
        "resource_title, resource_url, estimated_minutes. "
        f"Profile: {json.dumps(profile)}. "
        "Create realistic, personalized milestones and resources."
    )

    response = model.invoke(prompt)
    content = response.content if isinstance(response.content, str) else str(response.content)
    start_idx = content.find("{")
    end_idx = content.rfind("}")
    if start_idx == -1 or end_idx == -1:
        return None

    raw_json = content[start_idx : end_idx + 1]
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return None

    return _normalize_generated_plan(profile, parsed)


def build_skill_tree_and_schedule(profile: dict) -> dict:
    llm_plan = _llm_schedule(profile)
    if llm_plan:
        return llm_plan
    return _fallback_schedule(profile)
