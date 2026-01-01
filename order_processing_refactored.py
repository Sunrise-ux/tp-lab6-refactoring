"""
Модуль обработки заказов после рефакторинга.
"""

# Константы для устранения магических чисел
DEFAULT_CURRENCY = "USD"
DEFAULT_TAX_RATE = 0.21

# Коды купонов и их настройки
COUPON_SAVE10 = "SAVE10"
COUPON_SAVE10_RATE = 0.10

COUPON_SAVE20 = "SAVE20"
COUPON_SAVE20_RATE_HIGH = 0.20
COUPON_SAVE20_RATE_LOW = 0.05
COUPON_SAVE20_THRESHOLD = 200

COUPON_VIP = "VIP"
COUPON_VIP_DISCOUNT_HIGH = 50
COUPON_VIP_DISCOUNT_LOW = 10
COUPON_VIP_THRESHOLD = 100

# Константы для валидации
MIN_PRICE = 0
MIN_QUANTITY = 0


def parse_request(request: dict):
    """Извлекает данные из запроса с значениями по умолчанию."""
    user_id = request.get("user_id")
    items = request.get("items")
    coupon = request.get("coupon")
    currency = request.get("currency", DEFAULT_CURRENCY)
    return user_id, items, coupon, currency


def validate_request(user_id, items):
    """Проверяет корректность входных данных."""
    if user_id is None:
        raise ValueError("user_id is required")
    
    if items is None:
        raise ValueError("items is required")
    
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    
    if len(items) == 0:
        raise ValueError("items must not be empty")


def validate_items(items):
    """Проверяет корректность каждого товара в заказе."""
    for item in items:
        if "price" not in item or "qty" not in item:
            raise ValueError("item must have price and qty")
        
        if item["price"] <= MIN_PRICE:
            raise ValueError("price must be positive")
        
        if item["qty"] <= MIN_QUANTITY:
            raise ValueError("qty must be positive")


def calculate_subtotal(items):
    """Вычисляет общую стоимость товаров без скидок."""
    return sum(item["price"] * item["qty"] for item in items)


def calculate_discount(subtotal, coupon):
    """Вычисляет размер скидки на основе купона."""
    if not coupon:  # coupon is None or empty string
        return 0
    
    if coupon == COUPON_SAVE10:
        return int(subtotal * COUPON_SAVE10_RATE)
    
    if coupon == COUPON_SAVE20:
        discount_rate = (
            COUPON_SAVE20_RATE_HIGH if subtotal >= COUPON_SAVE20_THRESHOLD
            else COUPON_SAVE20_RATE_LOW
        )
        return int(subtotal * discount_rate)
    
    if coupon == COUPON_VIP:
        return (
            COUPON_VIP_DISCOUNT_HIGH if subtotal >= COUPON_VIP_THRESHOLD
            else COUPON_VIP_DISCOUNT_LOW
        )
    
    raise ValueError("unknown coupon")


def calculate_tax(amount, tax_rate=DEFAULT_TAX_RATE):
    """Вычисляет налог на указанную сумму."""
    return int(amount * tax_rate)


def generate_order_id(user_id, items_count):
    """Генерирует идентификатор заказа."""
    return f"{user_id}-{items_count}-X"


def ensure_non_negative(value):
    """Гарантирует, что значение не будет отрицательным."""
    return max(value, 0)


def process_checkout(request: dict) -> dict:
    """Обрабатывает запрос на оформление заказа."""
    # Шаг 1: Разбор запроса
    user_id, items, coupon, currency = parse_request(request)
    
    # Шаг 2: Валидация
    validate_request(user_id, items)
    validate_items(items)
    
    # Шаг 3: Расчёт стоимости
    subtotal = calculate_subtotal(items)
    
    # Шаг 4: Применение скидки
    discount = calculate_discount(subtotal, coupon)
    total_after_discount = ensure_non_negative(subtotal - discount)
    
    # Шаг 5: Расчёт налога и итога
    tax = calculate_tax(total_after_discount)
    total = total_after_discount + tax
    
    # Шаг 6: Формирование результата
    order_id = generate_order_id(user_id, len(items))
    
    return {
        "order_id": order_id,
        "user_id": user_id,
        "currency": currency,
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "total": total,
        "items_count": len(items),
    }
