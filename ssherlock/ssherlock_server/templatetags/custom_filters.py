from django import template

register = template.Library()


@register.filter
def get_attr(obj, attr_name):
    """Retrieve an attribute from an object by name."""
    return getattr(obj, attr_name, None)
