"""Custom template tags / filters for Harpr."""

from django import template

register = template.Library()


@register.filter
def cat_label(category_key, labels):
    """Return the user's renamed label for a category key."""
    if not category_key:
        return ""
    if isinstance(labels, dict):
        return labels.get(category_key, category_key.title())
    return category_key.title()


@register.filter
def cat_color(category_key, colors):
    if not category_key:
        return ""
    if isinstance(colors, dict):
        return colors.get(category_key, "#888888")
    return "#888888"


@register.filter
def get_item(d, key):
    if isinstance(d, dict):
        return d.get(key, "")
    return ""
