from django.conf import settings
import requests

def get_auth_token():
    url = "https://accept.paymob.com/api/auth/tokens"
    payload = {
        "api_key": settings.PAYMOB_API_KEY
    }
    response = requests.post(url, json=payload)
    response_data = response.json()
    return response_data["token"]


def create_order(auth_token, amount_cents, currency="EGP", items=[]):
    url = "https://accept.paymob.com/api/ecommerce/orders"
    payload = {
        "auth_token": auth_token,
        "delivery_needed": "false",
        "amount_cents": str(amount_cents),
        "currency": currency,
        "items": items
    }
    response = requests.post(url, json=payload)
    response_data = response.json()
    return response_data["id"]


def generate_payment_url(user_data, auth_token, order_id, integration_id, amount_cents):
    url = f"https://accept.paymob.com/api/acceptance/payment_keys"
    payload = {
        "auth_token": auth_token,
        "amount_cents": str(amount_cents),
        "expiration": 3600,
        "order_id": order_id,
        "billing_data": {
            "apartment": "NA",
            "email": "customer@example.com",
            "floor": "NA",
            "first_name": "John",
            "last_name": "Doe",
            "street": "123 Main St",
            "building": "NA",
            "phone_number": "+20123456789",
            "shipping_method": "NA",
            "postal_code": "NA",
            "city": "Cairo",
            "country": "EGY",
            "state": "NA"
        },
        "currency": "EGP",
        "integration_id": integration_id
    }
    response = requests.post(url, json=payload)
    response_data = response.json()
    return response_data["token"]
