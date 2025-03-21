"""Create the database"""
import json
DATA_FILE = "transactions.json"

"""Define the functions"""
def load_transactions():
    """Load transactions from JSON file"""
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
            return [] # Return empty list if file doesn't exist or is corrupt

def save_transactions(transactions):
    """Save transactions to JSON file"""
    with open(DATA_FILE, "w") as file:
        json.dump(transactions, file, indent=4)

def add_transaction(transactions, transaction_type):
    """Add an income or expense transaction"""
    category = input(f"Enter {transaction_type} category: (e.g., Salary, Food, Transport): ").strip()

    while True:
        try:
            amount = float(input(f"Enter {transaction_type} amount: ").strip())
            if amount < 0:
                raise ValueError("Amount must be positive")
            break
        except ValueError as e:
            print(f"Invalid input: {e}. Please enter a valid number.")

    transaction = {"category": category, "amount": amount, "type": transaction_type}
    transactions.append(transaction)
    save_transactions(transactions)
    print(f"{transaction_type.capitalize()} added successfully!")

def view_transactions(transactions):
    """Display all transactions"""
    print("\n===== Transactions =====")
    if not transactions:
        print("No transactions recorded.")
    else:
        for idx, t in enumerate(transactions, start=1):
            print(f"{idx}. {t['type'].capitalize()}: - {t['category']}: ${t['amount']:.2f}")

def show_balance(transactions):
    """Calculate and display total income, expenses, and balance"""
    income = sum(t['amount'] for t in transactions if t['type'] == 'Income')
    expenses = sum(t["amount"] for t in transactions if t['type'] == 'Expense')
    print(f"\nTotal income: {income:.2f}")
    print(f"Total expenses: {expenses:.2f}")
    print(f"Balance: ${income - expenses:.2f}")

    """Add a transaction to the database"""
def show_menu():
    print("\n----------Budget Tracker----------")
    print("1. Add Income")
    print("2. Add Expense")
    print("3. View Transactions")
    print("4. Show Balance")
    print("5. Exit")

def main():
    """Main program loop"""
    transactions = load_transactions()
    while True:
        show_menu()
        choice = input("Choose an option: ")
        if choice == "1":
            add_transaction(transactions, "Income")
        elif choice == "2":
            add_transaction(transactions, "Expense")
        elif choice == "3":
            view_transactions(transactions)
        elif choice == "4":
            show_balance(transactions)
        elif choice == "5":
            print("Goodbye")
            break

if __name__ == "__main__":
    main()