# Carrito y Lista de Deseos — localStorage

## Resumen

Sistema de carrito de compras y lista de deseos que funciona para usuarios **anónimos** (sin registro) y **registrados**, usando `localStorage` del navegador.

- **Usuario anónimo**: todo se guarda en `localStorage`. No se pierde al cerrar el navegador.
- **Usuario registrado**: al hacer login/registro, los datos de `localStorage` se pueden migrar a la base de datos (merge pendiente de implementar cuando existan los modelos `Cart` y `Wishlist` en backend).

---

## Archivos modificados / creados

### Creados

| Archivo | Descripcion |
|---|---|
| `partials/_store_js.html` | Motor JavaScript: objeto global `PL` con todas las funciones de carrito, wishlist, mini-cart, toasts y event delegation |
| `wishlist.html` | Pagina de lista de deseos (`/lista-de-deseos/`) — renderiza la wishlist desde localStorage, permite eliminar items y moverlos al carrito |

### Modificados

| Archivo | Cambio |
|---|---|
| `base.html` | Se incluye `_store_js.html` despues de `main.js` para que `PL` este disponible en todas las paginas |
| `home.html` | Se agregan atributos `data-pl-*` (id, name, slug, price, compare-price, image) a los `div.tp-product-item` de los 3 loops de productos (nuevos, destacados, mas vendidos) |
| `category.html` | Se agregan atributos `data-pl-*` al `div.tp-product-item-2` del loop de productos |
| `product_detail.html` | Se agrega `id="js-add-to-wishlist"` al boton de lista de deseos. Se agrega JS al final que conecta los botones "Agregar al carrito" y "Lista de deseos" con `PL.addToCart()` y `PL.addToWish()` |
| `partials/_header.html` | El icono de corazon ahora enlaza a `/lista-de-deseos/` y muestra badge con clase `pl-wish-count`. El badge del carrito ya se actualiza automaticamente via `tp-header-action-badge` |
| `partials/_offcanvas.html` | Links del menu movil: "Favoritos" apunta a `/lista-de-deseos/`, "Cuenta" apunta a perfil o login segun autenticacion |

### Backend (views/urls)

| Archivo | Cambio |
|---|---|
| `store/views.py` | Se agrega `wishlist_view` — renderiza `wishlist.html` |
| `store/urls.py` | Se agrega ruta `lista-de-deseos/` → `wishlist_view` con name `wishlist` |

---

## Como funciona paso a paso

### 1. Objeto global `PL` (`_store_js.html`)

Se carga en todas las paginas via `base.html`. Expone:

**Carrito:**
- `PL.addToCart(item)` — agrega producto (si ya existe, suma cantidad)
- `PL.removeFromCart(productId, variantId)` — elimina item
- `PL.updateCartQty(productId, variantId, qty)` — cambia cantidad
- `PL.getCart()` — retorna array del carrito
- `PL.getCartCount()` — total de unidades
- `PL.getCartTotal()` — suma de precios
- `PL.clearCart()` — vacia el carrito

**Wishlist:**
- `PL.addToWish(item)` — agrega a favoritos (no duplica)
- `PL.removeFromWish(productId)` — elimina de favoritos
- `PL.isInWish(productId)` — verifica si ya esta
- `PL.getWish()` — retorna array
- `PL.getWishCount()` — total de items

**Otros:**
- `PL.showToast(msg)` — notificacion flotante azul
- `PL.getMergeData()` — retorna `{cart, wishlist}` para enviar al backend en el merge
- `PL.clearAll()` — limpia todo (post-merge)

### 2. Tarjetas de producto (home, categoria)

Cada tarjeta tiene atributos `data-pl-*` en el div contenedor:

```html
<div class="tp-product-item"
     data-pl-id="123"
     data-pl-name="Producto X"
     data-pl-slug="producto-x"
     data-pl-price="59900"
     data-pl-compare-price="79900"
     data-pl-image="https://...">
```

Los botones `.tp-product-add-cart-btn` y `.tp-product-add-to-wishlist-btn` se manejan via **event delegation** en `_store_js.html` — no necesitan onclick individual.

### 3. Pagina de detalle de producto

Los botones `#js-add-to-cart` y `#js-add-to-wishlist` se conectan en el bloque `extra_js`:

- **Carrito**: lee la cantidad del input, busca la variante seleccionada (si aplica), y llama `PL.addToCart()` con todos los datos incluyendo variante, SKU y atributos.
- **Wishlist**: toggle — si ya esta, lo quita; si no, lo agrega. Cambia clase `active` en el boton.

### 4. Mini-carrito (sidebar)

El panel lateral `.cartmini__area` (en `_offcanvas.html`) se renderiza dinamicamente:
- `PL.renderMiniCart()` se llama cada vez que cambia el carrito
- Muestra imagen, nombre, precio x cantidad, y boton para eliminar
- El subtotal se actualiza en `.cartmini__checkout-title span`

### 5. Badges del header

- **Carrito**: `.tp-header-action-badge` — se actualiza automaticamente
- **Wishlist**: `.pl-wish-count` — se actualiza automaticamente

### 6. Pagina de lista de deseos (`/lista-de-deseos/`)

- Tabla con los productos guardados en localStorage
- Boton para agregar al carrito desde la wishlist
- Boton para eliminar de la wishlist
- Estado vacio con mensaje e icono

---

## Estructura de datos en localStorage

### Carrito (`pidelibre-cart`)

```json
[
  {
    "id": 123,
    "variantId": 456,
    "name": "Camiseta Azul",
    "slug": "camiseta-azul",
    "price": 59900,
    "comparePrice": 79900,
    "image": "https://bucket.s3.amazonaws.com/...",
    "qty": 2,
    "sku": "CAM-AZ-M",
    "attributes": {"Color": "Azul", "Talla": "M"}
  }
]
```

### Wishlist (`pidelibre-wishlist`)

```json
[
  {
    "id": 123,
    "name": "Camiseta Azul",
    "slug": "camiseta-azul",
    "price": 59900,
    "comparePrice": 79900,
    "image": "https://bucket.s3.amazonaws.com/..."
  }
]
```

---

## Merge al registrar/logear (futuro)

Cuando se implementen los modelos `Cart` y `Wishlist` en el backend:

1. Al hacer login/registro exitoso, llamar `PL.getMergeData()` en JavaScript
2. Enviar ese JSON al backend via AJAX (POST a un endpoint `/api/merge/`)
3. El backend guarda los items en la base de datos vinculados al usuario
4. Llamar `PL.clearAll()` para limpiar localStorage
5. A partir de ahi, las acciones de carrito/wishlist se hacen via AJAX al backend

---

## Clases CSS utilizadas

| Clase | Uso |
|---|---|
| `.tp-product-add-cart-btn` | Boton "agregar al carrito" en tarjetas (home, categoria) |
| `.tp-product-add-to-wishlist-btn` | Boton "favoritos" en tarjetas |
| `[data-pl-id]` | Contenedor de tarjeta con datos del producto |
| `.tp-header-action-badge` | Badge del carrito en el header |
| `.pl-wish-count` | Badge de wishlist en el header |
| `.pl-cart-count` | Badge alternativo de carrito |
| `#js-add-to-cart` | Boton carrito en detalle de producto |
| `#js-add-to-wishlist` | Boton wishlist en detalle de producto |
