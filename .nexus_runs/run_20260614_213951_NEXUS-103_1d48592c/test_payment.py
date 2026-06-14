# Test Suite for payment processing
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
