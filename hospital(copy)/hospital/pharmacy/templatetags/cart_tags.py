# pharmacy/templatetags/cart_tags.py
from django import template
from pharmacy.models import Cart

register = template.Library()

@register.simple_tag(takes_context=True)
def cart_item_count(context):
    request = context['request']
    user = request.user
    if not user.is_authenticated:
        return 0
    cart = Cart.objects.filter(user=user).first()
    if cart:
        return cart.items.count()
    return 0
