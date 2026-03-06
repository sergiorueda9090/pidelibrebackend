import json
from collections import OrderedDict
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Prefetch, Min, Case, When, F, Q, DecimalField
from category.models import Category
from product.models import Product, ProductImage, ProductVariant
from attribute_value.models import AttributeValue
from slider.models import Slider


def get_category_ids(category):
    """Devuelve el ID de la categoría y todos sus descendientes activos."""
    ids = [category.id]
    for child in category.children.filter(is_active=True, deleted_at__isnull=True):
        ids.extend(get_category_ids(child))
    return ids


def get_breadcrumb(category):
    """Devuelve la lista de categorías desde la raíz hasta la actual."""
    trail = []
    cat = category
    while cat:
        trail.insert(0, cat)
        cat = cat.parent
    return trail


def home(request):
    sliders = Slider.objects.filter(
        is_active=True, deleted_at__isnull=True
    ).select_related('product').order_by('order')

    return render(request, 'store/home.html', {
        'sliders': sliders,
    })


def category_view(request, slug):
    category     = get_object_or_404(Category, slug=slug, is_active=True, deleted_at__isnull=True)
    category_ids = get_category_ids(category)

    ordering = request.GET.get('ordering', 'newest')
    order_map = {
        'newest':     '-created_at',
        'oldest':     'created_at',
        'price_asc':  'effective_price',
        'price_desc': '-effective_price',
    }
    order_by = order_map.get(ordering, '-created_at')

    active_variants_qs = ProductVariant.objects.filter(
        is_active=True, deleted_at__isnull=True
    )

    products_qs = (
        Product.objects
        .filter(category_id__in=category_ids, is_active=True, deleted_at__isnull=True)
        .select_related('category')
        .prefetch_related(
            Prefetch('variants', queryset=active_variants_qs, to_attr='active_variants')
        )
        .annotate(
            _min_variant_price=Min(
                'variants__price',
                filter=Q(variants__is_active=True, variants__deleted_at__isnull=True),
            ),
            effective_price=Case(
                When(_min_variant_price__isnull=False, then=F('_min_variant_price')),
                default=F('price'),
                output_field=DecimalField(),
            ),
        )
        .order_by(order_by)
    )

    total     = products_qs.count()
    paginator = Paginator(products_qs, 12)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'store/category.html', {
        'category':  category,
        'breadcrumb': get_breadcrumb(category),
        'products':  page_obj,
        'total':     total,
        'ordering':  ordering,
        'page_obj':  page_obj,
    })


def product_detail_view(request, slug):
    active_variants_qs = (
        ProductVariant.objects
        .filter(is_active=True, deleted_at__isnull=True)
        .prefetch_related(
            Prefetch(
                'attribute_values',
                queryset=AttributeValue.objects.select_related('attribute').order_by('attribute__name', 'order'),
            )
        )
    )

    product = get_object_or_404(
        Product.objects
        .select_related('category', 'category__parent')
        .prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.order_by('order', 'created_at')),
            Prefetch('variants', queryset=active_variants_qs, to_attr='active_variants'),
        ),
        slug=slug,
        is_active=True,
        deleted_at__isnull=True,
    )

    # Construir lista unificada de imágenes (portada + galería + variantes)
    seen_urls = set()
    all_images = []

    if product.image:
        all_images.append(product.image)
        seen_urls.add(product.image.name)

    for img in product.images.all():
        if img.image.name not in seen_urls:
            all_images.append(img.image)
            seen_urls.add(img.image.name)

    for variant in product.active_variants:
        if variant.image and variant.image.name not in seen_urls:
            all_images.append(variant.image)
            seen_urls.add(variant.image.name)

    # Agrupar atributos de variantes: {"Color": [{"value": "Rojo", "color_hex": "#FF0000"}, ...], "Talla": [...]}
    variations = OrderedDict()
    for variant in product.active_variants:
        for av in variant.attribute_values.all():
            attr_name = av.attribute.name
            if attr_name not in variations:
                variations[attr_name] = []
            entry = {'value': av.value, 'color_hex': av.color_hex}
            if entry not in variations[attr_name]:
                variations[attr_name].append(entry)

    # Stock total: suma variantes si existen, sino usa stock del producto
    if product.active_variants:
        total_stock = sum(v.stock for v in product.active_variants)
    else:
        total_stock = product.stock or 0

    breadcrumb = get_breadcrumb(product.category) if product.category else []

    # Serializar datos de variantes para JS
    variants_data = []
    for v in product.active_variants:
        attrs = {}
        for av in v.attribute_values.all():
            attrs[av.attribute.name] = av.value
        variants_data.append({
            'id': v.id,
            'sku': v.sku or '',
            'price': int(v.price),
            'compare_price': int(v.compare_price) if v.compare_price else None,
            'stock': v.stock,
            'image_url': v.image.url if v.image else None,
            'attributes': attrs,
        })

    product_price = int(product.price) if product.price else 0
    product_compare_price = int(product.compare_price) if product.compare_price else None

    product_json = {
        'variants': variants_data,
        'product_price': product_price,
        'product_compare_price': product_compare_price,
        'product_stock': total_stock,
        'has_variants': bool(product.active_variants),
    }

    # Descuento inicial (server-side) para badge
    initial_discount = None
    cp = product.display_compare_price
    p = product.display_price
    if cp and p and cp > p:
        initial_discount = round((1 - float(p) / float(cp)) * 100)

    return render(request, 'store/product_detail.html', {
        'product':           product,
        'all_images':        all_images,
        'variations':        variations,
        'total_stock':       total_stock,
        'breadcrumb':        breadcrumb,
        'product_json':      json.dumps(product_json),
        'initial_discount':  initial_discount,
    })
