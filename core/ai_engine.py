"""
Mock AI Engine for Task Management System - V2
Provides: task suggestions, priority prediction, delay prediction,
workload auto-balancing, similarity detection, smart reminders, summaries.
"""

import random
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher


class AIEngine:
    """Mock AI engine that provides intelligent task management features."""

    TASK_TEMPLATES = {
        "textile": [
            "Review fabric quality reports for {month}",
            "Update inventory for {category} section",
            "Schedule vendor meeting for raw material procurement",
            "Prepare monthly sales analysis report",
            "Conduct quality inspection for new shipment",
            "Update pricing for seasonal collection",
            "Review and approve purchase orders",
            "Coordinate with logistics for delivery schedule",
            "Prepare staff training schedule for new procedures",
            "Audit warehouse stock levels",
        ],
        "general": [
            "Complete quarterly performance review",
            "Update standard operating procedures",
            "Review and respond to customer feedback",
            "Prepare budget proposal for next quarter",
            "Schedule team building activity",
            "Review compliance documentation",
            "Update employee handbook",
            "Plan departmental meeting agenda",
            "Review and approve expense reports",
            "Coordinate cross-department project",
        ],
    }

    PRIORITY_KEYWORDS = {
        "critical": ["urgent", "emergency", "critical", "immediately", "asap", "deadline today", "overdue"],
        "high": ["important", "priority", "soon", "this week", "client", "customer", "revenue"],
        "medium": ["review", "update", "prepare", "schedule", "plan", "coordinate"],
        "low": ["optional", "when possible", "future", "consider", "explore", "nice to have"],
    }

    SUMMARY_TEMPLATES = [
        "This task involves {action} related to {domain}. Key focus areas include {focus}. Estimated effort: {effort}.",
        "A {priority}-priority item requiring {action} in the {domain} area. This will impact {impact} and should be completed by the deadline.",
        "Task centered on {action} for {domain} operations. This is essential for {impact} and requires coordination with {team}.",
    ]

    @classmethod
    def suggest_tasks(cls, organization_name, existing_tasks=None, count=5):
        """Generate AI task suggestions based on organization context."""
        suggestions = []
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        categories = ["Cotton", "Silk", "Polyester", "Wool", "Linen", "Saree", "Dhoti", "Readymade"]
        current_month = months[datetime.now().month - 1]

        template_pool = cls.TASK_TEMPLATES["textile"] + cls.TASK_TEMPLATES["general"]
        random.shuffle(template_pool)

        existing_titles = set()
        if existing_tasks:
            existing_titles = {t.title.lower() for t in existing_tasks}

        for template in template_pool[:count * 2]:
            task_title = template.format(
                month=current_month,
                category=random.choice(categories),
            )
            if task_title.lower() not in existing_titles:
                priority = random.choice(["critical", "high", "medium", "medium", "low"])
                due_days = {"critical": 1, "high": 3, "medium": 7, "low": 14}
                suggestions.append({
                    "title": task_title,
                    "priority": priority,
                    "due_date": (datetime.now() + timedelta(days=due_days[priority])).strftime("%Y-%m-%d"),
                    "ai_reason": f"Suggested based on {organization_name}'s operational patterns and current period.",
                })
                if len(suggestions) >= count:
                    break

        return suggestions

    @classmethod
    def predict_priority(cls, title, description=""):
        """Predict task priority based on title and description content."""
        text = (title + " " + description).lower()

        for priority, keywords in cls.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return {
                        "predicted_priority": priority,
                        "confidence": round(random.uniform(0.75, 0.95), 2),
                        "reason": f"Contains keyword '{keyword}' indicating {priority} priority.",
                    }

        return {
            "predicted_priority": "medium",
            "confidence": round(random.uniform(0.6, 0.8), 2),
            "reason": "No strong priority indicators found. Defaulting to medium priority.",
        }

    @classmethod
    def generate_summary(cls, task):
        """Generate an AI summary for a task."""
        actions = ["reviewing and updating", "managing and coordinating",
                  "analyzing and reporting", "planning and executing",
                  "monitoring and improving"]
        domains = ["textile operations", "business management",
                  "quality assurance", "inventory management",
                  "customer relations", "supply chain"]
        focuses = ["accuracy and completeness", "timely delivery",
                  "cost optimization", "quality standards",
                  "team collaboration"]
        impacts = ["operational efficiency", "customer satisfaction",
                  "revenue growth", "process improvement",
                  "team productivity"]
        efforts = ["2-4 hours", "4-8 hours", "1-2 days", "2-3 days", "1 week"]
        teams = ["operations team", "management", "quality team",
                "sales department", "procurement team"]

        template = random.choice(cls.SUMMARY_TEMPLATES)
        summary = template.format(
            action=random.choice(actions),
            domain=random.choice(domains),
            focus=random.choice(focuses),
            impact=random.choice(impacts),
            effort=random.choice(efforts),
            priority=task.get("priority", "medium"),
            team=random.choice(teams),
        )
        return summary

    @classmethod
    def generate_subtasks(cls, task_title):
        """Generate subtasks for a given task."""
        subtask_templates = [
            ["Research and gather requirements", "Create action plan", "Execute primary tasks",
             "Review and validate results", "Document completion"],
            ["Analyze current state", "Identify improvements", "Implement changes",
             "Test and verify", "Report outcomes"],
            ["Collect relevant data", "Process and organize", "Review with stakeholders",
             "Make revisions", "Finalize and submit"],
        ]
        template = random.choice(subtask_templates)
        return [{"title": f"{st} for: {task_title[:50]}", "priority": "medium"} for st in template]

    @classmethod
    def chat_response(cls, message, org_name=""):
        """Generate an AI chat response for the assistant."""
        message_lower = message.lower()

        if any(w in message_lower for w in ["hello", "hi", "hey", "good"]):
            return f"Hello! I'm your AI assistant for {org_name or 'the organization'}. I can help you with:\n\n• **Task Suggestions** - Get smart task recommendations\n• **Priority Prediction** - Analyze task priority\n• **Task Summaries** - Generate task summaries\n• **Productivity Tips** - Improve your workflow\n\nHow can I help you today?"

        if any(w in message_lower for w in ["suggest", "recommend", "task idea", "what should"]):
            suggestions = cls.suggest_tasks(org_name, count=3)
            response = "Here are some task suggestions for you:\n\n"
            for i, s in enumerate(suggestions, 1):
                response += f"**{i}. {s['title']}**\n   Priority: {s['priority'].title()} | Due: {s['due_date']}\n\n"
            response += "Would you like me to create any of these tasks?"
            return response

        if any(w in message_lower for w in ["priority", "urgent", "important"]):
            prediction = cls.predict_priority(message)
            return (
                f"Based on my analysis:\n\n"
                f"**Predicted Priority:** {prediction['predicted_priority'].title()}\n"
                f"**Confidence:** {prediction['confidence'] * 100:.0f}%\n"
                f"**Reason:** {prediction['reason']}\n\n"
                f"Would you like me to adjust the priority of any existing tasks?"
            )

        if any(w in message_lower for w in ["report", "status", "summary", "overview"]):
            return (
                f"Here's a quick overview for {org_name or 'your organization'}:\n\n"
                f"📊 **Productivity Tip:** Focus on completing high-priority tasks first.\n"
                f"📅 **Suggestion:** Review overdue tasks and reschedule if needed.\n"
                f"👥 **Team Tip:** Ensure balanced task distribution among team members.\n\n"
                f"For detailed reports, check the Dashboard section."
            )

        if any(w in message_lower for w in ["help", "what can", "feature"]):
            return (
                "I can assist you with:\n\n"
                "1. **Task Suggestions** - Say 'suggest tasks' to get recommendations\n"
                "2. **Priority Analysis** - Describe a task and I'll predict its priority\n"
                "3. **Status Overview** - Ask for a 'status report'\n"
                "4. **Productivity Tips** - Ask for 'tips' to improve workflow\n"
                "5. **Task Breakdown** - Describe a complex task and I'll break it into subtasks\n\n"
                "Try asking me anything!"
            )

        if any(w in message_lower for w in ["tip", "productivity", "improve", "efficient"]):
            tips = [
                "🎯 **Focus Block:** Dedicate 2-hour blocks to deep work without interruptions.",
                "📋 **2-Minute Rule:** If a task takes less than 2 minutes, do it immediately.",
                "🔄 **Daily Review:** Spend 10 minutes each morning reviewing and prioritizing tasks.",
                "📊 **Track Progress:** Mark tasks complete as soon as they're done for accurate tracking.",
                "👥 **Delegate Wisely:** Assign tasks based on team members' strengths and availability.",
            ]
            return random.choice(tips) + "\n\nWant more productivity tips? Just ask!"

        if any(w in message_lower for w in ["break", "subtask", "split", "divide"]):
            subtasks = cls.generate_subtasks(message)
            response = "Here's how I'd break down this task:\n\n"
            for i, st in enumerate(subtasks, 1):
                response += f"**Step {i}:** {st['title']}\n"
            response += "\nWould you like me to create these as subtasks?"
            return response

        return (
            f"I understand you're asking about: *\"{message}\"*\n\n"
            f"I'm an AI assistant for {org_name or 'your organization'}. "
            f"I can help with task suggestions, priority predictions, summaries, and productivity tips.\n\n"
            f"Try saying:\n"
            f"• 'Suggest tasks for this week'\n"
            f"• 'What priority should [task description] be?'\n"
            f"• 'Give me a status report'\n"
            f"• 'Break down [task] into subtasks'"
        )

    # ================================================================
    # NEW V2 FEATURES
    # ================================================================

    @classmethod
    def predict_delay(cls, data):
        """Predict if a task is likely to be delayed based on various factors."""
        title = data.get("title", "")
        priority = data.get("priority", "medium")
        assignee_count = data.get("assignee_count", 1)
        days_until_due = data.get("days_until_due", 7)
        has_subtasks = data.get("has_subtasks", False)

        risk_score = 0.3  # base

        # Priority factor
        if priority == "critical":
            risk_score += 0.1
        elif priority == "low":
            risk_score += 0.15

        # Timeline pressure
        if days_until_due <= 1:
            risk_score += 0.3
        elif days_until_due <= 3:
            risk_score += 0.15
        elif days_until_due > 14:
            risk_score += 0.1  # long timeline => scope creep

        # Complexity indicators
        complex_words = ["audit", "review all", "comprehensive", "complete overhaul", "migrate", "redesign"]
        if any(w in title.lower() for w in complex_words):
            risk_score += 0.15

        # Multiple assignees => coordination overhead
        if assignee_count > 3:
            risk_score += 0.1

        # Subtasks complexity
        if has_subtasks:
            risk_score += 0.05

        risk_score = min(risk_score, 0.95)

        if risk_score > 0.7:
            risk_level = "high"
            suggestion = "Consider breaking this task into smaller parts or assigning additional resources."
        elif risk_score > 0.4:
            risk_level = "medium"
            suggestion = "Monitor progress closely. Set up intermediate checkpoints."
        else:
            risk_level = "low"
            suggestion = "Task appears manageable within the given timeline."

        return {
            "delay_probability": round(risk_score, 2),
            "risk_level": risk_level,
            "suggestion": suggestion,
            "factors": {
                "timeline_pressure": "high" if days_until_due <= 3 else "normal",
                "complexity": "high" if any(w in title.lower() for w in complex_words) else "normal",
                "team_size": assignee_count,
            },
            "confidence": round(random.uniform(0.70, 0.90), 2),
        }

    @classmethod
    def balance_workload(cls, org):
        """Analyze workload across team members and suggest rebalancing."""
        from core.models import UserProfile
        from tasks.models import Task

        members = UserProfile.objects.filter(organization=org, is_active=True).select_related("user")
        workload = []

        for m in members:
            active_tasks = Task.objects.filter(
                organization=org, assigned_to=m, is_trashed=False
            ).exclude(status="completed").count()

            total_points = Task.objects.filter(
                organization=org, assigned_to=m, is_trashed=False
            ).exclude(status="completed").values_list("points", flat=True)
            points_sum = sum(total_points)

            workload.append({
                "member_id": m.id,
                "name": m.full_name,
                "active_tasks": active_tasks,
                "total_points": points_sum,
            })

        if not workload:
            return {"suggestions": [], "summary": "No team members found."}

        avg_tasks = sum(w["active_tasks"] for w in workload) / len(workload)
        suggestions = []

        overloaded = [w for w in workload if w["active_tasks"] > avg_tasks * 1.5]
        underloaded = [w for w in workload if w["active_tasks"] < avg_tasks * 0.5]

        for over in overloaded:
            excess = over["active_tasks"] - int(avg_tasks)
            if underloaded:
                target = random.choice(underloaded)
                suggestions.append({
                    "type": "redistribute",
                    "from_member": over["name"],
                    "to_member": target["name"],
                    "task_count": min(excess, 3),
                    "reason": f"{over['name']} has {over['active_tasks']} tasks (avg: {avg_tasks:.0f}). "
                              f"Consider moving {min(excess, 3)} tasks to {target['name']}.",
                })

        return {
            "workload": workload,
            "average_tasks": round(avg_tasks, 1),
            "suggestions": suggestions,
            "summary": f"{len(overloaded)} overloaded, {len(underloaded)} underloaded out of {len(workload)} members.",
            "confidence": round(random.uniform(0.75, 0.90), 2),
        }

    @classmethod
    def find_similar_tasks(cls, org, title, description="", threshold=0.6):
        """Find similar tasks to avoid duplicates."""
        from tasks.models import Task

        existing = Task.objects.filter(
            organization=org, is_trashed=False
        ).values("id", "title", "description", "status")[:200]

        similar = []
        input_text = (title + " " + description).lower()

        for t in existing:
            task_text = (t["title"] + " " + (t["description"] or "")).lower()
            ratio = SequenceMatcher(None, input_text, task_text).ratio()

            # Also check title-only similarity
            title_ratio = SequenceMatcher(None, title.lower(), t["title"].lower()).ratio()
            final_ratio = max(ratio, title_ratio)

            if final_ratio >= threshold:
                similar.append({
                    "task_id": t["id"],
                    "title": t["title"],
                    "status": t["status"],
                    "similarity": round(final_ratio * 100, 1),
                })

        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar[:5]

    @classmethod
    def generate_smart_reminders(cls, org):
        """Generate smart reminders based on task patterns and deadlines."""
        from tasks.models import Task
        from django.utils import timezone

        now = timezone.now()
        reminders = []

        # Overdue tasks
        overdue = Task.objects.filter(
            organization=org, is_trashed=False,
            due_date__lt=now,
        ).exclude(status="completed").select_related("created_by")[:10]

        for t in overdue:
            days_overdue = (now - t.due_date).days
            reminders.append({
                "type": "overdue",
                "task_id": t.id,
                "title": t.title,
                "message": f"This task is {days_overdue} days overdue. Consider updating status or extending deadline.",
                "priority": "high" if days_overdue > 3 else "medium",
            })

        # Tasks due soon (next 24h)
        due_soon = Task.objects.filter(
            organization=org, is_trashed=False,
            due_date__range=[now, now + timedelta(hours=24)],
        ).exclude(status="completed")[:10]

        for t in due_soon:
            reminders.append({
                "type": "due_soon",
                "task_id": t.id,
                "title": t.title,
                "message": f"Due within 24 hours. Current status: {t.get_status_display()}.",
                "priority": "high",
            })

        # Stale in-progress tasks (no update for 3+ days)
        stale = Task.objects.filter(
            organization=org, is_trashed=False,
            status="in_progress",
            updated_at__lt=now - timedelta(days=3),
        )[:10]

        for t in stale:
            days_stale = (now - t.updated_at).days
            reminders.append({
                "type": "stale",
                "task_id": t.id,
                "title": t.title,
                "message": f"In progress for {days_stale} days without updates. Check progress.",
                "priority": "medium",
            })

        return reminders
