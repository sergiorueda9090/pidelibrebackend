import json
from collections import OrderedDict
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Prefetch, Min, Case, When, F, Q, DecimalField
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from category.models import Category
from product.models import Product, ProductImage, ProductVariant
from attribute_value.models import AttributeValue
from slider.models import Slider
from tp_feature_area.models import TpFeatureArea
from customer.models import Customer, CustomerAddress
from user.models import User


def custom_404(request, exception):
    return render(request, 'store/404.html', status=404)


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

    features = TpFeatureArea.objects.filter(
        is_active=True, deleted_at__isnull=True
    ).order_by('order')

    active_variants_qs = ProductVariant.objects.filter(
        is_active=True, deleted_at__isnull=True
    )
    base_products = (
        Product.objects
        .filter(is_active=True, deleted_at__isnull=True)
        .select_related('category')
        .prefetch_related(
            Prefetch('variants', queryset=active_variants_qs, to_attr='active_variants')
        )
    )

    new_products      = base_products.filter(is_new=True).order_by('-created_at')[:8]
    featured_products = base_products.filter(is_featured=True).order_by('-created_at')[:8]
    top_sellers       = base_products.order_by('-created_at')[:8]

    return render(request, 'store/home.html', {
        'sliders': sliders,
        'features': features,
        'new_products': new_products,
        'featured_products': featured_products,
        'top_sellers': top_sellers,
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


def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:profile')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '')
        password2  = request.POST.get('password2', '')

        if not all([first_name, last_name, email, password]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'store/register.html')

        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'store/register.html')

        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'store/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe una cuenta con este correo electrónico.')
            return render(request, 'store/register.html')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        Customer.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        login(request, user)
        messages.success(request, 'Cuenta creada exitosamente.')
        return redirect('store:profile')

    return render(request, 'store/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:profile')

    if request.method == 'POST':
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'store:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Correo electrónico o contraseña incorrectos.')

    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('store:home')


@login_required(login_url='/cuenta/ingresar/')
def profile_view(request):
    customer, _ = Customer.objects.get_or_create(
        user=request.user,
        defaults={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
    )
    address = customer.addresses.first()

    active_tab = request.POST.get('tab', request.GET.get('tab', 'profile'))

    if request.method == 'POST':
        tab = request.POST.get('tab', 'info')

        if tab == 'info':
            customer.first_name      = request.POST.get('first_name', customer.first_name).strip()
            customer.last_name       = request.POST.get('last_name', customer.last_name).strip()
            customer.phone           = request.POST.get('phone', '').strip() or None
            customer.document_number = request.POST.get('document_number', '').strip() or None
            customer.save()
            request.user.first_name = customer.first_name
            request.user.last_name  = customer.last_name
            request.user.save()
            messages.success(request, 'Información actualizada correctamente.')

        elif tab == 'address':
            addr_data = {
                'address':     request.POST.get('address', '').strip(),
                'city':        request.POST.get('city', '').strip(),
                'state':       request.POST.get('state', '').strip(),
                'country':     request.POST.get('country', 'Colombia').strip(),
                'postal_code': request.POST.get('postal_code', '').strip(),
            }
            if address:
                for key, val in addr_data.items():
                    setattr(address, key, val)
                address.save()
            else:
                address = CustomerAddress.objects.create(customer=customer, **addr_data)
            messages.success(request, 'Dirección actualizada correctamente.')

        elif tab == 'password':
            current  = request.POST.get('current_password', '')
            new_pass = request.POST.get('new_password', '')
            new_pass2 = request.POST.get('new_password2', '')

            if not request.user.check_password(current):
                messages.error(request, 'La contraseña actual es incorrecta.')
            elif new_pass != new_pass2:
                messages.error(request, 'Las nuevas contraseñas no coinciden.')
            elif len(new_pass) < 6:
                messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres.')
            else:
                request.user.set_password(new_pass)
                request.user.save()
                login(request, request.user)
                messages.success(request, 'Contraseña actualizada correctamente.')

        return redirect(f'/cuenta/perfil/?tab={tab}')

    return render(request, 'store/profile.html', {
        'customer': customer,
        'address': address,
        'active_tab': active_tab,
        'orders': [],
    })
