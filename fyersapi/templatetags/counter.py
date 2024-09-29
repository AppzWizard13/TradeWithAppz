from django import template

register = template.Library()

@register.simple_tag
def initialize_counter():
    return {'value': 0}

@register.simple_tag
def increment_counter(counter):
    counter['value'] += 1
    return ''

@register.filter
def subtract(value, arg):
    try:
        return value - arg
    except (TypeError, ValueError):
        return ''

