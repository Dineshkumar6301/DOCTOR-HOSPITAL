# pharmacy/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """
    Multiplies two numbers in a template.
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def split(value, delimiter=","):
    """
    Splits a string by the given delimiter.
    Usage: {% for part in some_string|split:"," %}
    """
    return value.split(delimiter)
