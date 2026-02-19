from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def multiply(value, arg):
    """Multiply value by argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage."""
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError):
        return 0


@register.filter
def status_badge_class(status):
    """Return Tailwind CSS classes for status badge."""
    classes = {
        "todo": "bg-gray-100 text-gray-700",
        "in_progress": "bg-blue-100 text-blue-700",
        "review": "bg-purple-100 text-purple-700",
        "completed": "bg-green-100 text-green-700",
        "on_hold": "bg-orange-100 text-orange-700",
        "scheduled": "bg-cyan-100 text-cyan-700",
        "overdue": "bg-red-100 text-red-700",
        "open": "bg-red-100 text-red-700",
        "resolved": "bg-green-100 text-green-700",
        "ignored": "bg-gray-100 text-gray-700",
        "closed": "bg-blue-100 text-blue-700",
        "active": "bg-blue-100 text-blue-700",
        "archived": "bg-gray-100 text-gray-700",
        "saved": "bg-yellow-100 text-yellow-700",
        "published": "bg-green-100 text-green-700",
        "trashed": "bg-red-100 text-red-700",
    }
    return classes.get(status, "bg-gray-100 text-gray-700")


@register.filter
def priority_badge_class(priority):
    """Return Tailwind CSS classes for priority badge."""
    classes = {
        "critical": "bg-red-100 text-red-700",
        "high": "bg-orange-100 text-orange-700",
        "medium": "bg-yellow-100 text-yellow-700",
        "low": "bg-green-100 text-green-700",
        "none": "bg-gray-100 text-gray-700",
    }
    return classes.get(priority, "bg-gray-100 text-gray-700")


@register.filter
def status_label(status):
    """Return human-readable status label."""
    labels = {
        "todo": "To Do",
        "in_progress": "In Progress",
        "review": "In Review",
        "completed": "Completed",
        "on_hold": "On Hold",
    }
    return labels.get(status, status)


@register.filter
def priority_label(priority):
    """Return human-readable priority label."""
    labels = {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }
    return labels.get(priority, priority)


@register.simple_tag
def active_class(request, pattern):
    """Return 'active' class if current path matches pattern."""
    import re
    if re.search(pattern, request.path):
        return "bg-indigo-50 text-indigo-700 border-r-2 border-indigo-600"
    return "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
