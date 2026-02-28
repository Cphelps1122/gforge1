# utils/formatting.py

def money(x):
    """
    Format any numeric value as $X,XXX.XX.
    Returns '-' for None/NaN/invalid values.
    """
    try:
        return f"${float(x):,.2f}"
    except:
        return "-"
