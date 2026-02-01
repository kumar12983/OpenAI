"""
Stripe payment integration for Premium subscriptions
"""
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

payments_bp = Blueprint('payments', __name__)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
PREMIUM_PRICE_ID = os.getenv('STRIPE_PREMIUM_PRICE_ID')
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')


def get_db_connection():
    """Import from app.py"""
    from app import get_db_connection as _get_db
    return _get_db()


@payments_bp.route('/checkout')
@login_required
def checkout():
    """Premium checkout page"""
    return render_template('checkout.html', 
                         stripe_publishable_key=STRIPE_PUBLISHABLE_KEY,
                         user=current_user)


@payments_bp.route('/api/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for Premium subscription"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get or create Stripe customer
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={'user_id': current_user.user_id}
            )
            
            # Save Stripe customer ID
            cursor.execute("""
                UPDATE webapp.users 
                SET stripe_customer_id = %s 
                WHERE user_id = %s
            """, (customer.id, current_user.user_id))
            conn.commit()
            customer_id = customer.id
        else:
            customer_id = current_user.stripe_customer_id
        
        cursor.close()
        conn.close()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': PREMIUM_PRICE_ID,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'pricing',
            metadata={'user_id': current_user.user_id}
        )
        
        return jsonify({'sessionId': checkout_session.id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@payments_bp.route('/payment/success')
@login_required
def payment_success():
    """Payment success page"""
    session_id = request.args.get('session_id')
    return render_template('payment_success.html', session_id=session_id)


@payments_bp.route('/api/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle subscription events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    
    return jsonify({'status': 'success'})


def handle_checkout_session_completed(session):
    """Upgrade user to Premium when payment succeeds"""
    user_id = session['metadata']['user_id']
    customer_id = session['customer']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE webapp.users 
            SET tier_id = 2,
                stripe_customer_id = %s,
                subscription_status = 'active',
                subscription_start_date = CURRENT_TIMESTAMP
            WHERE user_id = %s
        """, (customer_id, user_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error upgrading user {user_id}: {e}")
    finally:
        cursor.close()
        conn.close()


def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    customer_id = subscription['customer']
    status = subscription['status']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE webapp.users 
            SET subscription_status = %s
            WHERE stripe_customer_id = %s
        """, (status, customer_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating subscription for customer {customer_id}: {e}")
    finally:
        cursor.close()
        conn.close()


def handle_subscription_deleted(subscription):
    """Downgrade user when subscription is cancelled"""
    customer_id = subscription['customer']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE webapp.users 
            SET tier_id = 1,
                subscription_status = 'cancelled',
                subscription_end_date = CURRENT_TIMESTAMP
            WHERE stripe_customer_id = %s
        """, (customer_id,))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error downgrading user for customer {customer_id}: {e}")
    finally:
        cursor.close()
        conn.close()


@payments_bp.route('/api/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user's Premium subscription"""
    if not current_user.stripe_customer_id:
        return jsonify({'error': 'No active subscription'}), 400
    
    try:
        # Get customer's subscriptions
        subscriptions = stripe.Subscription.list(customer=current_user.stripe_customer_id)
        
        for subscription in subscriptions.data:
            if subscription.status == 'active':
                # Cancel at period end (not immediately)
                stripe.Subscription.modify(
                    subscription.id,
                    cancel_at_period_end=True
                )
        
        return jsonify({'success': True, 'message': 'Subscription will be cancelled at period end'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
