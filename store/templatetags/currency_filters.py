from django import template

register = template.Library()


@register.filter
def cop(value):
    """Formatea un número como peso colombiano: 329000 → $329.000"""
    if value is None:
        return ''
    try:
        amount = int(value)
    except (ValueError, TypeError):
        return value
    formatted = f'{amount:,}'.replace(',', '.')
    return f'${formatted}'
