

import csv
import os
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation


# Required timestamp format:
# yyyy-mm-ddThh:mm:ss
TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
)


def validate_timestamp(timestamp):
    """
    Validate that timestamp follows:
        yyyy-mm-ddThh:mm:ss

    Also checks whether the date and time are actually valid.
    """

    if not TIMESTAMP_PATTERN.fullmatch(timestamp):
        return False

    try:
        datetime.strptime(
            timestamp,
            "%Y-%m-%dT%H:%M:%S"
        )
        return True

    except ValueError:
        return False


def validate_transaction(row):
    """
    Validate one CSV transaction row.

    Returns:
        (True, "") when valid
        (False, reason) when invalid
    """

    # A valid transaction must contain exactly five fields.
    if len(row) != 5:
        return (
            False,
            f"Expected 5 fields, found {len(row)}"
        )

    transaction_id = row[0].strip()
    account_id = row[1].strip()
    transaction_type = row[2].strip()
    amount_text = row[3].strip()
    timestamp = row[4].strip()

    # -------------------------------------------------------------
    # Validate transaction ID.
    # -------------------------------------------------------------
    if not transaction_id:
        return False, "transaction_id is empty"

    # -------------------------------------------------------------
    # Validate account ID.
    # -------------------------------------------------------------
    if not account_id:
        return False, "account_id is empty"

    # -------------------------------------------------------------
    # Validate transaction type.
    # -------------------------------------------------------------
    if transaction_type not in ("CREDIT", "DEBIT"):
        return (
            False,
            "type must be CREDIT or DEBIT"
        )

    # -------------------------------------------------------------
    # Validate amount.
    # Decimal is used instead of float for monetary values.
    # -------------------------------------------------------------
    try:
        amount = Decimal(amount_text)

    except InvalidOperation:
        return False, "amount is not numeric"

    # Reject NaN and Infinity.
    if not amount.is_finite():
        return False, "amount must be a finite number"

    if amount <= 0:
        return False, "amount must be greater than 0"

    # -------------------------------------------------------------
    # Validate timestamp.
    # -------------------------------------------------------------
    if not validate_timestamp(timestamp):
        return (
            False,
            "timestamp must be yyyy-mm-ddThh:mm:ss"
        )

    return True, ""


def format_amount(amount):
    """
    Convert Decimal amount to a clean string for output.

    Examples:
        500      -> 500
        100.50   -> 100.50
        10.0     -> 10.0
    """

    return format(amount, "f")


def process_csv_file(input_path):
    """
    Process the input CSV file.

    Returns:
        account_balances dictionary containing account-wise
        net balance changes.
    """

    if not os.path.isfile(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    account_balances = {}

    with open(
        input_path,
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as input_file:

        reader = csv.reader(input_file)

        # ---------------------------------------------------------
        # Read header.
        # ---------------------------------------------------------
        try:
            header = next(reader)

        except StopIteration:
            raise ValueError("Input CSV file is empty.")

        # The problem specifies five columns.
        if len(header) != 5:
            raise ValueError(
                "CSV header must contain exactly 5 columns."
            )

        # ---------------------------------------------------------
        # Open output files.
        # ---------------------------------------------------------
        with open(
            "credit.csv",
            "w",
            newline="",
            encoding="utf-8"
        ) as credit_file, open(
            "debit.csv",
            "w",
            newline="",
            encoding="utf-8"
        ) as debit_file, open(
            "error.csv",
            "w",
            newline="",
            encoding="utf-8"
        ) as error_file:

            credit_writer = csv.writer(credit_file)
            debit_writer = csv.writer(debit_file)
            error_writer = csv.writer(error_file)

            # Preserve the original input header in valid files.
            credit_writer.writerow(header)
            debit_writer.writerow(header)

            # Error file contains original fields + reason.
            error_writer.writerow(
                list(header) + ["reason"]
            )

            # -----------------------------------------------------
            # Process every transaction.
            # -----------------------------------------------------
            for line_number, row in enumerate(reader, start=2):

                try:
                    is_valid, reason = validate_transaction(row)

                    if not is_valid:

                        # Invalid row is written to error.csv.
                        error_writer.writerow(
                            list(row) + [reason]
                        )

                        # Continue with the next row.
                        continue

                    transaction_id = row[0].strip()
                    account_id = row[1].strip()
                    transaction_type = row[2].strip()
                    amount = Decimal(row[3].strip())
                    timestamp = row[4].strip()

                    # -------------------------------------------------
                    # Store the valid row in its corresponding file.
                    # -------------------------------------------------
                    if transaction_type == "CREDIT":

                        credit_writer.writerow([
                            transaction_id,
                            account_id,
                            transaction_type,
                            format_amount(amount),
                            timestamp
                        ])

                    else:

                        debit_writer.writerow([
                            transaction_id,
                            account_id,
                            transaction_type,
                            format_amount(amount),
                            timestamp
                        ])

                    # -------------------------------------------------
                    # Update account-wise balance.
                    #
                    # CREDIT -> positive
                    # DEBIT  -> negative
                    # -------------------------------------------------
                    if account_id not in account_balances:
                        account_balances[account_id] = Decimal("0")

                    if transaction_type == "CREDIT":
                        account_balances[account_id] += amount
                    else:
                        account_balances[account_id] -= amount

                except (ValueError, InvalidOperation, TypeError) as error:

                    # Unexpected row-level error should not stop the
                    # processing of the remaining transactions.
                    error_writer.writerow(
                        list(row) + [f"Processing error: {error}"]
                    )

    return account_balances


def print_summary(account_balances):
    """
    Print account-wise balance changes.

    Accounts are sorted by:
        1. Descending absolute balance change.
        2. Lexicographically ascending account ID for ties.
    """

    sorted_accounts = sorted(
        account_balances.items(),
        key=lambda item: (
            -abs(item[1]),
            item[0]
        )
    )

    for account_id, balance in sorted_accounts:

        print(
            f"{account_id} {format_amount(balance)}"
        )


def main():
    """
    Main program.

    The input CSV path can be supplied as:
        python program.py transactions.csv

    If no command-line argument is supplied, the program asks
    for the path through standard input.
    """

    try:

        # ---------------------------------------------------------
        # Prefer command-line argument.
        # This makes the program convenient to run in VS Code,
        # terminal, etc.
        # ---------------------------------------------------------
        if len(sys.argv) >= 2:

            input_path = sys.argv[1].strip()

        else:

            input_path = input(
                "Enter input CSV file path: "
            ).strip()

        if not input_path:
            print("ERROR: Input file path cannot be empty.")
            return

        account_balances = process_csv_file(
            input_path
        )

        print_summary(account_balances)

        print("Files created: credit.csv, debit.csv, error.csv")

    except FileNotFoundError as error:

        print(f"ERROR: {error}")

    except PermissionError:

        print(
            "ERROR: Permission denied while accessing the file."
        )

    except csv.Error as error:

        print(f"ERROR: Invalid CSV format: {error}")

    except ValueError as error:

        print(f"ERROR: {error}")

    except OSError as error:

        print(f"ERROR: File operation failed: {error}")


if __name__ == "__main__":
    main()

"""
Programming with Python (202044504)
Assignment 1 - Question 4

Exception-Safe CSV Transaction Splitter

Python Version: 3.10+
External Packages: None

Input:
    Path of input CSV file.

Output:
    credit.csv
    debit.csv
    error.csv

The program:
    1. Reads the input CSV.
    2. Validates every transaction.
    3. Writes valid CREDIT transactions to credit.csv.
    4. Writes valid DEBIT transactions to debit.csv.
    5. Writes invalid transactions and their reasons to error.csv.
    6. Calculates account-wise net balance changes.
"""
