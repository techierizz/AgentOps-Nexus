# Template database for resetting target codebase files
import os
import shutil
import subprocess

PAYMENT_PROCESSOR_TEMPLATE = """# AgentOps Nexus - Demo Target Repository
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
"""

STRIPE_CLIENT_TEMPLATE = """# Stripe Client API Mock
def charge_card(amount: float) -> str:
    if amount <= 0:
        return "Zero Amount - Skipped"
    return f"Charged ${amount:.2f} via Stripe API Successfully"
"""

TEST_PAYMENT_TEMPLATE = """# Test Suite for payment processing
import pytest
import os
import sys

# Ensure local path is prioritized
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from payment_processor import PaymentProcessor

def test_successful_checkout():
    processor = PaymentProcessor()
    # 2 items, $50 order
    res = processor.process_order(50.0, 2)
    assert res["success"] is True
    assert res["fee"] == 2.5

def test_zero_items_division():
    processor = PaymentProcessor()
    # Cart item count is 0, should not crash with ZeroDivisionError
    res = processor.process_order(0.0, 0)
    assert res["success"] is True
    assert res["fee"] == 0.0

def test_stripe_import_loading():
    # Test that stripe modules load without ImportError crashing runtime
    import payment_processor
    # If dynamic import succeeds, Stripe charging should be active
    assert payment_processor.stripe is not None

def test_invalid_coupon_type_error():
    processor = PaymentProcessor()
    # Invalid coupon should return 0 discount instead of throwing TypeError
    res = processor.process_order(30.0, 1, "INVALIDCODE")
    assert res["success"] is True
    assert res["amount"] == 30.0
"""

DEMO_ISSUES = [
    {
        "id": "NEXUS-101",
        "title": "ZeroDivisionError in calculate_fees() on checkout",
        "description": "When checkout occurs for free promotional items (where total cost and cart items are 0), the system crashes with a ZeroDivisionError. Stack trace:\n\n```python\nTraceback (most recent call last):\n  File \"test_payment.py\", line 15, in test_zero_items_division\n    res = processor.process_order(0.0, 0)\n  File \"payment_processor.py\", line 45, in process_order\n    fee = self.calculate_fees(5.0, items)\n  File \"payment_processor.py\", line 21, in calculate_fees\n    fee_per_item = total_fee / total_items\nZeroDivisionError: division by zero\n```"
    },
    {
        "id": "NEXUS-102",
        "title": "ImportError loading Stripe connector dynamic module",
        "description": "The checkout page fails to process stripe transactions and test cases fail with an import error. The Stripe module fails to dynamically bind. Stack trace:\n\n```python\nTraceback (most recent call last):\n  File \"test_payment.py\", line 22, in test_stripe_import_loading\n    assert payment_processor.stripe is not None\nAssertionError: assert None is not None\n```\n\nNote: The dynamic import loads `stripe_gateway` but the local file is actually named `stripe_client.py`."
    },
    {
        "id": "NEXUS-103",
        "title": "TypeError: 'NoneType' object is not subscriptable on coupon checkout",
        "description": "Applying an invalid discount code causes a crash because the coupon loader returns None. Stack trace:\n\n```python\nTraceback (most recent call last):\n  File \"test_payment.py\", line 28, in test_invalid_coupon_type_error\n    res = processor.process_order(30.0, 1, \"INVALIDCODE\")\n  File \"payment_processor.py\", line 41, in process_order\n    discount = self.apply_discount(discount_code)\n  File \"payment_processor.py\", line 28, in apply_discount\n    discount_val = self.get_coupon_map(code)['value']\nTypeError: 'NoneType' object is not subscriptable\n```"
    }
]

def reset_target_repository(repo_path: str):
    """Wipes and recreates the target demo repository files in their buggy state."""
    repo_path = os.path.abspath(repo_path)
    
    # If the directory already exists, clear everything except the .git directory (if it exists)
    if os.path.exists(repo_path):
        for item in os.listdir(repo_path):
            item_path = os.path.join(repo_path, item)
            if item == ".git":
                continue
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
    else:
        os.makedirs(repo_path)

    # Write target files
    with open(os.path.join(repo_path, "payment_processor.py"), "w", encoding="utf-8") as f:
        f.write(PAYMENT_PROCESSOR_TEMPLATE)
        
    with open(os.path.join(repo_path, "stripe_client.py"), "w", encoding="utf-8") as f:
        f.write(STRIPE_CLIENT_TEMPLATE)
        
    with open(os.path.join(repo_path, "test_payment.py"), "w", encoding="utf-8") as f:
        f.write(TEST_PAYMENT_TEMPLATE)

    # If it is a git repo, reset modifications or checkout main
    git_dir = os.path.join(repo_path, ".git")
    if os.path.exists(git_dir):
        try:
            # Re-checkout main and discard changes
            subprocess.run(["git", "checkout", "main"], cwd=repo_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=repo_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "clean", "-fdx"], cwd=repo_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
