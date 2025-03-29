import hashlib

class Transaction:
    def __init__(self, trans_date, text, amount, balance=None, category=None):
        self.trans_date = trans_date
        self.text = text
        self.amount = float(amount)
        self.balance = float(balance) if balance is not None else None
        self.category = category
        self.trans_hash = self.generate_hash()

    def generate_hash(self):
        """Generate a unique hash based on transaction fields."""
        unique_string = f"{self.trans_date}_{self.text}_{self.amount}"
        return hashlib.sha256(unique_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "trans_date": self.trans_date,
            "text": self.text,
            "amount": self.amount,
            "balance": self.balance,
            "category": self.category,
            "trans_hash": self.trans_hash
        }
    
    def __repr__(self):
        return f"Transaction(trans_date={self.trans_date}, amount={self.amount}, text={self.text} )"
