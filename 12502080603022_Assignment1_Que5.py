

import sys



class BankError(Exception):
    """Base exception for bank-related errors."""


class AccountNotFoundError(BankError):
    """Raised when an account does not exist."""


class InvalidAmountError(BankError):
    """Raised when an amount is invalid."""


class InsufficientFundsError(BankError):
    """Raised when an account does not have enough funds."""


class SameAccountError(BankError):
    """Raised when a transfer has the same source and destination."""


class BatchError(BankError):
    """Raised when an invalid batch operation occurs."""



class Account:
    """
    Represents a bank account.

    The balance is kept private to provide encapsulation.
    """

    def __init__(self, account_id, balance):
        self._account_id = account_id
        self._balance = balance

    @property
    def account_id(self):
        """Return the account ID."""
        return self._account_id

    @property
    def balance(self):
        """Return the current account balance."""
        return self._balance

    def deposit(self, amount):
        """Deposit a positive amount into the account."""

        if amount <= 0:
            raise InvalidAmountError(
                "Amount must be greater than zero."
            )

        self._balance += amount

    def withdraw(self, amount):
        """Withdraw an amount without allowing overdraft."""

        if amount <= 0:
            raise InvalidAmountError(
                "Amount must be greater than zero."
            )

        if amount > self._balance:
            raise InsufficientFundsError(
                f"Insufficient funds in account {self._account_id}."
            )

        self._balance -= amount

    def set_balance(self, balance):
        """
        Set the account balance.

        This is used internally by the Bank class during rollback.
        """

        if balance < 0:
            raise ValueError("Balance cannot be negative.")

        self._balance = balance



class Transaction:
    """
    Represents one successfully executed transaction.

    Transaction history is maintained by the Bank class.
    """

    def __init__(
        self,
        transaction_type,
        account_id,
        amount,
        target_account=None
    ):
        self.transaction_type = transaction_type
        self.account_id = account_id
        self.amount = amount
        self.target_account = target_account

    def __str__(self):
        """Return a readable transaction description."""

        if self.transaction_type == "TRANSFER":
            return (
                f"TRANSFER {self.account_id} "
                f"{self.target_account} {self.amount}"
            )

        return (
            f"{self.transaction_type} "
            f"{self.account_id} {self.amount}"
        )



class Bank:
    """
    Manages accounts, transactions and batches.
    """

    def __init__(self):
        self._accounts = {}
        self._transaction_history = []

        # None means that no batch is currently active.
        self._active_batch = None

        # Number of the current batch.
        self._batch_counter = 0

        # Stores batch numbers that were rolled back.
        self._failed_batches = []

    

    def add_account(self, account_id, balance):
        """Add a new account."""

        if account_id in self._accounts:
            raise BankError(
                f"Duplicate account: {account_id}"
            )

        if balance < 0:
            raise InvalidAmountError(
                "Initial balance cannot be negative."
            )

        self._accounts[account_id] = Account(
            account_id,
            balance
        )

    def get_account(self, account_id):
        """Return an account or raise an exception."""

        if account_id not in self._accounts:
            raise AccountNotFoundError(
                f"Account {account_id} does not exist."
            )

        return self._accounts[account_id]


    def _create_snapshot(self):
        """
        Create a snapshot of all account balances.

        A dictionary is sufficient because account IDs are unique.
        """

        return {
            account_id: account.balance
            for account_id, account in self._accounts.items()
        }

    def _restore_snapshot(self, snapshot):
        """Restore all account balances from a snapshot."""

        for account_id, balance in snapshot.items():
            self._accounts[account_id].set_balance(balance)

    

    def _record_transaction(self, transaction):
        """Store a successful transaction in history."""

        self._transaction_history.append(transaction)

    

    def deposit(self, account_id, amount):
        """Deposit money into an account."""

        account = self.get_account(account_id)

        account.deposit(amount)

        transaction = Transaction(
            "DEPOSIT",
            account_id,
            amount
        )

        self._record_transaction(transaction)

        return transaction

    

    def withdraw(self, account_id, amount):
        """Withdraw money from an account."""

        account = self.get_account(account_id)

        account.withdraw(amount)

        transaction = Transaction(
            "WITHDRAW",
            account_id,
            amount
        )

        self._record_transaction(transaction)

        return transaction

    
    def transfer(
        self,
        source_account_id,
        target_account_id,
        amount
    ):
        """Transfer money between two accounts."""

        if source_account_id == target_account_id:
            raise SameAccountError(
                "Source and destination accounts must differ."
            )

        source = self.get_account(source_account_id)
        target = self.get_account(target_account_id)

        # Withdraw first. If it fails, the target is untouched.
        source.withdraw(amount)
        target.deposit(amount)

        transaction = Transaction(
            "TRANSFER",
            source_account_id,
            amount,
            target_account_id
        )

        self._record_transaction(transaction)

        return transaction

   

    def begin_batch(self):
        """Start a new transaction batch."""

        if self._active_batch is not None:
            raise BatchError(
                "A batch is already active."
            )

        self._batch_counter += 1

        self._active_batch = {
            "number": self._batch_counter,
            "snapshot": self._create_snapshot(),
            "history_length": len(self._transaction_history)
        }

    
    def end_batch(self):
        """
        Finish the current batch.

        A valid batch is committed.

        Invalid transactions are handled by execute_operation(),
        which rolls back the batch.
        """

        if self._active_batch is None:
            raise BatchError(
                "No active batch."
            )

        self._active_batch = None

   

    def rollback_batch(self):
        """Rollback the current batch completely."""

        if self._active_batch is None:
            return

        batch_number = self._active_batch["number"]
        snapshot = self._active_batch["snapshot"]
        history_length = self._active_batch["history_length"]

        # Restore every account balance.
        self._restore_snapshot(snapshot)

        # Remove transactions created inside the failed batch.
        del self._transaction_history[history_length:]

        self._failed_batches.append(batch_number)

        self._active_batch = None

  
    def execute_operation(self, operation):
        """
        Execute one operation.

        If an operation fails inside a batch, the entire batch
        is rolled back.
        """

        parts = operation.split()

        if not parts:
            raise ValueError("Empty operation.")

        command = parts[0]

        try:

          
            if command == "DEPOSIT":

                if len(parts) != 3:
                    raise ValueError(
                        "DEPOSIT requires account and amount."
                    )

                account_id = parts[1]
                amount = self._parse_amount(parts[2])

                self.deposit(account_id, amount)

           
            elif command == "WITHDRAW":

                if len(parts) != 3:
                    raise ValueError(
                        "WITHDRAW requires account and amount."
                    )

                account_id = parts[1]
                amount = self._parse_amount(parts[2])

                self.withdraw(account_id, amount)

            
            elif command == "TRANSFER":

                if len(parts) != 4:
                    raise ValueError(
                        "TRANSFER requires source, target and amount."
                    )

                source = parts[1]
                target = parts[2]
                amount = self._parse_amount(parts[3])

                self.transfer(
                    source,
                    target,
                    amount
                )

            else:
                raise ValueError(
                    f"Unknown operation: {command}"
                )

        except Exception:

            # If an operation fails while a batch is active,
            # rollback EVERYTHING done in that batch.
            if self._active_batch is not None:
                self.rollback_batch()

                # The failure is intentionally swallowed here
                # because the required output is FAILED <batch>.
                return False

            # Operations outside a batch are not rolled back.
            raise

        return True

    

    @staticmethod
    def _parse_amount(value):
        """Convert and validate a transaction amount."""

        try:
            amount = int(value)
        except ValueError:
            raise InvalidAmountError(
                "Amount must be an integer."
            )

        if amount <= 0:
            raise InvalidAmountError(
                "Amount must be greater than zero."
            )

        return amount

   
    def print_balances(self):
        """Print final balances in account ID order."""

        for account_id in sorted(self._accounts):
            account = self._accounts[account_id]

            print(
                f"{account_id} {account.balance}"
            )

    @property
    def failed_batches(self):
        """Return failed batch numbers."""

        return list(self._failed_batches)



def process_input(data):
    """
    Process complete input and return output lines.

    This function is separated from main() so that the solution
    can be tested without depending on interactive input.
    """

    lines = [
        line.strip()
        for line in data.splitlines()
        if line.strip()
    ]

    if not lines:
        raise ValueError("Input is empty.")

    position = 0

    try:
        account_count = int(lines[position])
    except ValueError:
        raise ValueError(
            "Number of accounts must be an integer."
        )

    position += 1

    if not (1 <= account_count <= 100000):
        raise ValueError(
            "Invalid number of accounts."
        )

    bank = Bank()

    
    for _ in range(account_count):

        if position >= len(lines):
            raise ValueError(
                "Missing account data."
            )

        parts = lines[position].split()
        position += 1

        if len(parts) != 2:
            raise ValueError(
                "Account format must be: account_id balance."
            )

        account_id = parts[0]

        try:
            balance = int(parts[1])
        except ValueError:
            raise ValueError(
                "Account balance must be an integer."
            )

        if balance < 0:
            raise ValueError(
                "Account balance cannot be negative."
            )

        bank.add_account(
            account_id,
            balance
        )

   
    if position >= len(lines):
        raise ValueError(
            "Missing operation count."
        )

    try:
        operation_count = int(lines[position])
    except ValueError:
        raise ValueError(
            "Operation count must be an integer."
        )

    position += 1

    if not (1 <= operation_count <= 300000):
        raise ValueError(
            "Invalid operation count."
        )

    if len(lines) - position < operation_count:
        raise ValueError(
            "Not enough operations."
        )

    output = []

   
    for _ in range(operation_count):

        operation = lines[position]
        position += 1

        command = operation.split()[0]

        if command == "BATCH_BEGIN":

            if len(operation.split()) != 1:
                raise ValueError(
                    "BATCH_BEGIN takes no arguments."
                )

            bank.begin_batch()

        elif command == "BATCH_END":

            if len(operation.split()) != 1:
                raise ValueError(
                    "BATCH_END takes no arguments."
                )

            bank.end_batch()

        else:

            success = bank.execute_operation(
                operation
            )

            if not success:
                # The failed batch number is the latest failed batch.
                failed_number = bank.failed_batches[-1]

                output.append(
                    f"FAILED {failed_number}"
                )

    # A batch cannot remain open after all operations.
    if bank._active_batch is not None:
        raise ValueError(
            "Input ended before BATCH_END."
        )

    # Final account balances.
    for account_id in sorted(bank._accounts):
        output.append(
            f"{account_id} "
            f"{bank._accounts[account_id].balance}"
        )

    return output



def main():
    """Read input from stdin and print the result."""

    try:
        data = sys.stdin.read()

        if not data.strip():
            print("INVALID")
            return

        result = process_input(data)

        for line in result:
            print(line)

    except (ValueError, OSError) as error:
        print(f"INVALID: {error}")


if __name__ == "__main__":
    main()

    """
Programming with Python (202044504)
Assignment 1 - Question 5

Object-Oriented Bank Settlement System

Python Version: 3.10+
External Packages: None

Features:
    - Account class
    - Transaction class
    - Bank class
    - Deposit
    - Withdrawal
    - Transfer
    - Transaction history
    - Overdraft prevention
    - Batch processing
    - Complete batch rollback on failure
    - Custom exceptions
"""
