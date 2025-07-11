# Stripe Payment Integration Demo

This is a simple Stripe payment integration for your Flask chat application. It demonstrates how to accept payments using Stripe's payment intents API.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Stripe Keys

1. Sign up for a Stripe account at https://stripe.com
2. Get your test API keys from the Stripe Dashboard
3. Replace the dummy keys in the `.env` file with your actual test keys:

```env
STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_actual_secret_key_here
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### 3. Run the Application

```bash
python web_chat.py
```

The application will be available at `http://localhost:5000`

## Features

### Payment Demo
- **Payment Page**: `/payment?amount=2000` - Shows a payment form for $20.00
- **Success Page**: `/success` - Shows after successful payment
- **Cancel Page**: `/cancel` - Shows when payment is cancelled

### Test Payment Amounts
The chat interface includes demo buttons for different amounts:
- $10.00 (1000 cents)
- $20.00 (2000 cents)
- $50.00 (5000 cents)
- $100.00 (10000 cents)

## How It Works

### 1. Payment Flow
1. User clicks a payment button on the chat page
2. They're taken to `/payment` with the amount as a query parameter
3. The payment page loads Stripe Elements for secure card input
4. When submitted, a payment intent is created on the server
5. The payment is confirmed using Stripe's client-side confirmation
6. User is redirected to success or cancel page based on the result

### 2. API Endpoints
- `POST /create-payment-intent` - Creates a Stripe payment intent
- `GET /payment` - Shows the payment form
- `GET /success` - Shows success page with payment details
- `GET /cancel` - Shows cancellation page

## Testing

### Test Card Numbers
Use these test card numbers for testing:

- **Successful Payment**: `4242 4242 4242 4242`
- **Declined Payment**: `4000 0000 0000 0002`
- **Requires Authentication**: `4000 0025 0000 3155`

### Test CVC and Expiry
- **CVC**: Any 3 digits (e.g., `123`)
- **Expiry**: Any future date (e.g., `12/25`)

## Security Notes

- Never commit real Stripe keys to version control
- Always use test keys for development
- The `.env` file is included in `.gitignore` to prevent accidental commits
- In production, use environment variables or a secure configuration management system

## Files Structure

```
├── web_chat.py              # Main Flask application
├── stripe_payment.py        # Stripe utility functions
├── .env                     # Environment variables (create this)
├── requirements.txt         # Python dependencies
├── templates/
│   ├── chat.html           # Main chat interface with payment buttons
│   ├── payment.html        # Stripe payment form
│   ├── success.html        # Payment success page
│   └── cancel.html         # Payment cancellation page
└── README_STRIPE.md        # This file
```

## Customization

### Changing Payment Amounts
Modify the payment demo buttons in `templates/chat.html`:

```html
<a href="/payment?amount=1500" class="payment-demo">Pay $15.00</a>
```

### Styling
The payment pages use custom CSS. You can modify the styles in the respective template files to match your brand.

### Adding More Payment Methods
To add more payment methods (like Apple Pay, Google Pay), modify the Stripe Elements configuration in `templates/payment.html`.

## Troubleshooting

### Common Issues

1. **"No such file or directory: '.env'"**
   - Make sure you've created the `.env` file with your Stripe keys

2. **"Invalid API key provided"**
   - Check that your Stripe keys are correct and in the right format
   - Make sure you're using test keys, not live keys

3. **Payment fails with "Your card was declined"**
   - This is expected behavior with test cards like `4000 0000 0000 0002`
   - Use `4242 4242 4242 4242` for successful test payments

4. **"Module not found" errors**
   - Run `pip install -r requirements.txt` to install dependencies

### Getting Help

- Check the Stripe documentation: https://stripe.com/docs
- Review the Stripe test mode guide: https://stripe.com/docs/testing
- Check the Flask application logs for detailed error messages 