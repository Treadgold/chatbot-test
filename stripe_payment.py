import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

def create_payment_intent(amount, currency='nzd'):
    """Create a payment intent with Stripe"""
    try:
        intent = stripe.PaymentIntent.create(
            amount=amount,  # Amount in cents
            currency=currency,
            automatic_payment_methods={'enabled': True},
        )
        return intent
    except Exception as e:
        print(f"Error creating payment intent: {e}")
        return None

def create_checkout_session(amount, currency='nzd', success_url=None, cancel_url=None):
    """Create a checkout session with Stripe"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': 'Demo Product',
                    },
                    'unit_amount': amount,  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url or 'http://localhost:5000/success',
            cancel_url=cancel_url or 'http://localhost:5000/cancel',
        )
        return session
    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return None

def get_payment_intent(payment_intent_id):
    """Retrieve a payment intent from Stripe"""
    try:
        return stripe.PaymentIntent.retrieve(payment_intent_id)
    except Exception as e:
        print(f"Error retrieving payment intent: {e}")
        return None 