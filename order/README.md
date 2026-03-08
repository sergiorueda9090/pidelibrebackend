# Módulo de Órdenes y Pasarela de Pago

## Resumen

Este módulo gestiona todo el flujo de compra: desde que el cliente hace clic en "Realizar Pedido" hasta que el pago es confirmado por la pasarela (Mercado Pago).

---

## Flujo Completo

```
┌──────────────────────────────────────────────────────────────────────┐
│                        FLUJO DE COMPRA                               │
└──────────────────────────────────────────────────────────────────────┘

  CLIENTE (Browser)                  BACKEND (Django)                  MERCADO PAGO
  ─────────────────                  ────────────────                  ────────────

  1. Llena formulario
     de checkout
         │
         ▼
  2. Click "Realizar Pedido"
         │
         │  POST /api/order/create/
         │  { customer, items, payment_method }
         │
         ▼
                                   3. ¿Existe Customer
                                      con ese email?
                                      │
                                 ┌────┴────┐
                                 │ SÍ      │ NO
                                 │         │
                                 │    Crea User (sin
                                 │    contraseña) +
                                 │    Customer nuevo
                                 └────┬────┘
                                      │
                                   4. Valida stock de
                                      cada producto
                                      (select_for_update)
                                      │
                                 ┌────┴────┐
                                 │ OK      │ SIN STOCK
                                 │         │
                                 │    Retorna error ──────► "Stock insuficiente
                                 │    HTTP 409               para Producto X"
                                 │
                                   5. Resta stock de
                                      Product/Variant
                                      │
                                   6. Crea Order +
                                      OrderItems +
                                      Payment (pending)
                                      │
                                   7. Crea Preference ───────► Mercado Pago
                                      en Mercado Pago          recibe los items,
                                      │                        montos y URLs
                                      │
                                   8. Retorna              ◄── Retorna init_point
                                      { redirect_url }         (URL de pago)
                                      │
         ◄─────────────────────────────┘
         │
  9. Redirect automático
     a Mercado Pago
         │
         ▼
                                                              10. Cliente paga
                                                                  en Mercado Pago
                                                                  │
                                                              ┌───┴───┐
                                                              │       │
                                                           Aprobado  Rechazado
                                                              │       │
         ◄────── Redirect a /checkout/resultado/ ─────────────┘       │
         │       ?order=PL-20260307-XXXX                              │
         │                                                            │
  11. Ve página de                                                    │
      resultado                                                       │
      (aprobado/pendiente)                                            │
                                                                      │
                                  12. Webhook POST ◄──────────────────┘
                                      /api/order/webhooks/mercadopago/
                                      │
                                  13. Consulta el pago
                                      en la API de MP
                                      │
                                  14. Actualiza:
                                      - Payment.status
                                      - Order.status
                                      │
                                  15. ¿Rechazado?
                                      SÍ → Restaura stock
                                      NO → Stock ya descontado
```

---

## Modelos de Datos

### Order (Orden)

| Campo | Tipo | Descripción |
|---|---|---|
| `order_number` | CharField | Auto-generado: `PL-20260307-A1B2C3` |
| `customer` | FK → Customer | Cliente asociado |
| `email` | EmailField | Email del comprador (snapshot) |
| `first_name` | CharField | Nombre (snapshot) |
| `last_name` | CharField | Apellido (snapshot) |
| `phone` | CharField | Teléfono |
| `document_number` | CharField | CC / NIT |
| `address`, `city`, `state`, `country`, `postal_code` | CharField | Dirección de envío |
| `notes` | TextField | Notas del pedido |
| `status` | CharField | Estado actual (ver abajo) |
| `payment_method` | CharField | `wompi`, `mercadopago`, `paypal` |
| `subtotal` | Decimal | Suma de items |
| `shipping_cost` | Decimal | Costo de envío |
| `total` | Decimal | subtotal + shipping_cost |

### OrderItem (Ítem de la orden)

| Campo | Tipo | Descripción |
|---|---|---|
| `order` | FK → Order | Orden padre |
| `product` | FK → Product | Referencia al producto (puede ser NULL si se elimina) |
| `variant` | FK → ProductVariant | Variante comprada (opcional) |
| `product_name` | CharField | Nombre al momento de la compra (snapshot) |
| `product_image` | URLField | URL de la imagen (snapshot) |
| `sku` | CharField | SKU del producto/variante |
| `attributes` | JSONField | `{"Color": "Rojo", "Talla": "M"}` |
| `price` | Decimal | Precio unitario al momento de la compra |
| `quantity` | Integer | Cantidad comprada |
| `total` | Decimal | price × quantity (auto-calculado) |

### Payment (Pago)

| Campo | Tipo | Descripción |
|---|---|---|
| `order` | FK → Order | Orden asociada |
| `provider` | CharField | `mercadopago`, `wompi`, `paypal` |
| `transaction_id` | CharField | ID de la transacción en la pasarela |
| `status` | CharField | `pending`, `approved`, `rejected`, `refunded` |
| `amount` | Decimal | Monto pagado |
| `raw_response` | JSONField | Respuesta completa de la pasarela (para debug) |

---

## Estados de una Orden

```
                    ┌─────────────────┐
                    │ PENDING_PAYMENT │  ← Estado inicial al crear la orden
                    │ (Pendiente de   │
                    │  pago)          │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │  APPROVED  │  │  REJECTED  │  │ CANCELLED  │
     │ (Aprobado) │  │(Rechazado) │  │(Cancelado) │
     └──────┬─────┘  └────────────┘  └────────────┘
            │          Stock se         Stock se
            │          RESTAURA         RESTAURA
            ▼
     ┌────────────┐
     │  SHIPPED   │
     │ (Enviado)  │  ← Admin marca manualmente
     └──────┬─────┘
            │
            ▼
     ┌────────────┐
     │ DELIVERED  │
     │(Entregado) │  ← Admin marca manualmente
     └────────────┘
```

### Qué pasa con el stock en cada transición

| Transición | Acción |
|---|---|
| → `PENDING_PAYMENT` | **Se resta** el stock (reserva) |
| → `APPROVED` | Nada (ya fue restado) |
| → `REJECTED` | **Se restaura** el stock |
| → `CANCELLED` | **Se restaura** el stock |
| → `SHIPPED` | Nada |
| → `DELIVERED` | Nada |

---

## Endpoints API

| Método | URL | Auth | Descripción |
|---|---|---|---|
| `POST` | `/api/order/create/` | No | Crear orden desde checkout |
| `GET` | `/api/order/detail/<order_number>/` | No | Ver detalle de una orden |
| `GET` | `/api/order/all/` | Sí | Listar todas las órdenes (admin) |
| `GET` | `/api/order/reports/sales/` | Sí | Reporte de ventas |
| `POST` | `/api/order/webhooks/mercadopago/` | No* | Webhook de Mercado Pago |

*El webhook no requiere auth de Django, Mercado Pago lo llama directamente.

### POST `/api/order/create/` — Body esperado

```json
{
  "customer": {
    "first_name": "Carlos",
    "last_name": "García",
    "email": "carlos@email.com",
    "phone": "3001234567",
    "document_number": "1234567890",
    "address": "Calle 50 #30-20",
    "address2": "Apto 301",
    "city": "Medellín",
    "state": "ANTIOQUIA",
    "country": "Colombia",
    "postal_code": "050001",
    "notes": "Entregar en la portería"
  },
  "items": [
    {
      "id": 5,
      "variantId": 12,
      "name": "Camiseta Roja Talla M",
      "price": 45000,
      "qty": 2,
      "image": "https://bucket.s3.amazonaws.com/product_image/abc.jpg",
      "sku": "CAM-ROJA-M",
      "attributes": {"Color": "Rojo", "Talla": "M"}
    }
  ],
  "payment_method": "mercadopago",
  "shipping_cost": 10000
}
```

### Respuesta exitosa (HTTP 201)

```json
{
  "order_number": "PL-20260307-A1B2C3",
  "total": 100000,
  "redirect_url": "https://www.mercadopago.com.co/checkout/v1/redirect?pref_id=xxx"
}
```

### Respuesta con error de stock (HTTP 409)

```json
{
  "error": "Stock insuficiente para \"Camiseta Roja – CAM-ROJA-M\". Disponible: 1, solicitado: 2"
}
```

---

## Auto-registro de Clientes

Cuando un cliente compra **sin estar registrado**:

1. Se busca un `Customer` con ese email
2. Si **no existe**:
   - Se crea un `User` con `set_unusable_password()` (sin contraseña)
   - Se crea un `Customer` vinculado a ese User
   - Se guarda su dirección
3. Si **ya existe**: se actualiza su info y se asocia la orden

El cliente puede después ir a **"Olvidé mi contraseña"** para establecer una contraseña y acceder a su cuenta.

---

## Configuración de Mercado Pago

### 1. Crear cuenta en Mercado Pago

Ir a [mercadopago.com.co](https://www.mercadopago.com.co) → Crear cuenta de desarrollador.

### 2. Obtener credenciales

En [mercadopago.com.co/developers](https://www.mercadopago.com.co/developers/panel/app) → Tu aplicación → Credenciales:

- **Access Token** (privado, va en el backend)
- **Public Key** (público, va en el frontend si se necesita)

### 3. Agregar al `.env`

```env
MERCADOPAGO_ACCESS_TOKEN=APP_USR-xxxxxxxxxxxx-xxxxxx-xxxxxxxxxxxx-xxxxxxxxxx
MERCADOPAGO_PUBLIC_KEY=APP_USR-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SITE_URL=https://tu-dominio.com
```

> Para pruebas locales con webhook, usa [ngrok](https://ngrok.com/) para exponer tu `localhost:8000`:
> ```bash
> ngrok http 8000
> ```
> Y usa la URL de ngrok como `SITE_URL`.

### 4. Configurar webhook en Mercado Pago

En el panel de desarrollador → Webhooks → Agregar:
- **URL**: `https://tu-dominio.com/api/order/webhooks/mercadopago/`
- **Eventos**: `payment`

---

## Reporte de Ventas

`GET /api/order/reports/sales/` retorna:

```json
{
  "total_orders": 150,
  "total_revenue": 15000000,
  "orders_by_status": {
    "approved": 120,
    "pending_payment": 10,
    "shipped": 15,
    "delivered": 5
  },
  "top_products": [
    {
      "product_name": "Camiseta Deportiva",
      "units_sold": 45,
      "revenue": 2250000
    },
    {
      "product_name": "Pantalón Casual",
      "units_sold": 30,
      "revenue": 1800000
    }
  ]
}
```

---

## Estructura de Archivos

```
backend/order/
├── models.py              # Order, OrderItem, Payment
├── services.py            # Lógica: crear orden, stock, Mercado Pago
├── admin.py               # Admin con inlines
├── api/
│   ├── views.py           # Endpoints REST
│   ├── serializers.py     # Serializers DRF
│   └── urls.py            # Rutas /api/order/
├── migrations/
│   └── 0001_initial.py    # Migración de tablas
└── README.md              # Este archivo

Archivos modificados:
├── backend/settings.py    # +order en INSTALLED_APPS, +config MP
├── backend/urls.py        # +path api/order/
├── store/urls.py          # +path checkout/resultado/
├── store/views.py         # +checkout_result_view()
└── store/templates/store/
    ├── checkout.html       # placeOrder() conectado al backend
    └── checkout_result.html # Página post-pago
```
