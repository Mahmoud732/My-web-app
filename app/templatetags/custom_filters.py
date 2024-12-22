# myapp/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_token_for_order(tokens, order_id):
    token = tokens.filter(order_id=order_id).first()
    return token.token if token else ''

@register.filter
def truncate_chars(value, arg):
    try:
        length = int(arg)
    except ValueError:
        return value
    if len(value) > length:
        return value[:length] + "..."
    return value
