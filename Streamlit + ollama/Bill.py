import hashlib

class Bill:
    def __init__(self, creditor, date, amount, recurring=False):
        self.creditor = creditor
        self.date = date
        self.amount = float(amount.replace(",", ".")) if amount else None
        self.recurring = recurring
        self.id = self.generate_id()

    def generate_id(self):
        """Generate a unique ID based on creditor and date."""
        unique_string = f"{self.creditor}_{self.date}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def to_dict(self):
        """Convert to dictionary for easy storage/display."""
        return {
            "id": self.id,
            "creditor": self.creditor,
            "date": self.date,
            "amount": self.amount,
            "recurring": self.recurring
        }
        
      
    def __repr__(self):
        return f"Bill(creditor={self.creditor}, date={self.date}, amount={self.amount}, recurring={self.recurring})"
