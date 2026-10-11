def sustained_decline(balances):
    """Three successive declines, >=20% cumulative fall, >=10k baseline."""
    if len(balances) < 4:
        return False
    a, b, c, d = balances[-4:]
    return bool(a >= 10000 and a > b > c > d and d <= a * 0.80)


def cross_sell(holdings, sales, deposits):
    """Illustrative signals, not credit decisions or calibrated recommendations."""
    return {
        "merchant_cross_sell": not holdings["has_merchant_services"] and sales >= 50000,
        "payroll_cross_sell": not holdings["has_payroll_services"] and sales >= 80000,
        "treasury_cross_sell": not holdings["has_treasury_services"]
        and deposits >= 200000,
        "card_cross_sell": not holdings["has_credit_card"] and sales >= 25000,
    }
