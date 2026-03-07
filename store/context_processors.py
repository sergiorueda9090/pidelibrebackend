from django.conf import settings
from django.db.models import Prefetch
from category.models import Category
from footer.models import Footer


def categories(request):
    """Inyecta el árbol de categorías activas en todos los templates (header, offcanvas)."""
    active = dict(is_active=True, deleted_at__isnull=True)

    grandchildren_qs = (
        Category.objects
        .filter(**active)
        .order_by('order', 'name')
    )

    children_qs = (
        Category.objects
        .filter(**active)
        .prefetch_related(Prefetch('children', queryset=grandchildren_qs))
        .order_by('order', 'name')
    )

    cats = (
        Category.objects
        .filter(**active, parent__isnull=True)
        .prefetch_related(Prefetch('children', queryset=children_qs))
        .order_by('order', 'name')
    )

    footer = Footer.objects.filter(is_active=True, deleted_at__isnull=True).first()

    return {
        'categories': cats,
        'footer': footer,
        'S3_DOMAIN': getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', ''),
    }
