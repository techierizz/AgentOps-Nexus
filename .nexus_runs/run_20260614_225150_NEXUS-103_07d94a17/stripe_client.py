# Stripe Client API Mock
def charge_card(amount: float) -> str:
    if amount <= 0:
        return "Zero Amount - Skipped"
    return f"Charged ${amount:.2f} via Stripe API Successfully"
