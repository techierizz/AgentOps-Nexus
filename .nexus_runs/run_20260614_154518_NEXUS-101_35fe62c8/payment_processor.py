# AgentOps Nexus - Demo Target Repository
import os
import sys

# Bug 2: ImportError
# The code tries to load 'stripe_gateway', but the actual file name is 'stripe_client.py'
try:
    import stripe_gateway as stripe
except ImportError:
    # Dynamic import attempt representing conditional production code
    stripe = None

class PaymentProcessor:
    def __init__(self):
        self.transactions = []

    def calculate_fees(self, total_fee: float, total_items: int) -> float:
        # Bug 1: ZeroDivisionError
        # When order total is zero (e.g. free product promotions), total_items is 0.
        # This division throws a ZeroDivisionError.
        fee_per_item = total_fee / total_items
        return fee_per_item

    def apply_discount(self, code: str) -> float:
        # Bug 3: TypeError
        # If code is invalid or expired, get_coupon_map returns None.
        # Accessing ['value'] on None raises a TypeError.
        discount_val = self.get_coupon_map(code)['value']
        return discount_val

    def get_coupon_map(self, code: str):
        # Mock coupon database
        coupons = {
            "SAVE10": {"code": "SAVE10", "value": 10.0},
            "SUMMER20": {"code": "SUMMER20", "value": 20.0}
        }
        return coupons.get(code, None) # Returns None if not found

    def process_order(self, amount: float, items: int, discount_code: str = None) -> dict:
        discount = 0.0
        if discount_code:
            discount = self.apply_discount(discount_code)
            
        final_amount = max(0.0, amount - discount)
        fee = self.calculate_fees(5.0, items) if final_amount > 0 else 0.0
        
        # Stripe payment simulation
        stripe_status = "Skipped"
        if stripe:
            stripe_status = stripe.charge_card(final_amount)
            
        return {
            "success": True,
            "amount": final_amount,
            "fee": fee,
            "stripe": stripe_status
        }
