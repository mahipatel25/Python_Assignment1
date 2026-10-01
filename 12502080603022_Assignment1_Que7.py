import re
import sys


class FormulaError(Exception):
    """Base class for formula-related errors."""


class InvalidFormatError(FormulaError):
    """Raised when the formula format is invalid."""


class UnknownVariableError(FormulaError):
    """Raised when a variable has not been defined."""


class DivisionByZeroError(FormulaError):
    """Raised when division or modulo uses zero."""


class UnsupportedOperatorError(FormulaError):
    """Raised when an unsupported operator is used."""



VARIABLE_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)

NUMBER_PATTERN = re.compile(
    r"^(?:\d+(?:\.\d*)?|\.\d+)$"
)




def is_valid_variable_name(name):
    """Return True if name follows Python identifier-style rules."""

    return bool(
        VARIABLE_PATTERN.fullmatch(name)
    )


def parse_number(value):
    """
    Convert a string to int or float.

    Integer values remain integers.
    Decimal values become floats.
    """

    if not NUMBER_PATTERN.fullmatch(value):
        raise InvalidFormatError(
            f"Invalid operand: {value}"
        )

    try:

        if "." in value:
            return float(value)

        return int(value)

    except ValueError:
        raise InvalidFormatError(
            f"Invalid numeric value: {value}"
        )


def get_operand_value(operand, variables):
    """
    Resolve an operand.

    It may be:
        - an integer
        - a decimal
        - a previously stored variable
    """

    
    if NUMBER_PATTERN.fullmatch(operand):

        return parse_number(operand)

    
    if is_valid_variable_name(operand):

        if operand not in variables:
            raise UnknownVariableError(
                f"Unknown variable: {operand}"
            )

        return variables[operand]

    raise InvalidFormatError(
        f"Invalid operand: {operand}"
    )



def calculate(left, operator, right):
    """
    Perform the requested arithmetic operation.

    Supported operators:
        +
        -
        *
        /
        %
    """

    if operator == "+":

        return left + right

    if operator == "-":

        return left - right

    if operator == "*":

        return left * right

    if operator == "/":

        if right == 0:
            raise DivisionByZeroError(
                "Cannot divide by zero."
            )

        return left / right

    if operator == "%":

        if right == 0:
            raise DivisionByZeroError(
                "Cannot calculate modulo by zero."
            )

        return left % right

    raise UnsupportedOperatorError(
        f"Unsupported operator: {operator}"
    )


def evaluate_formula(formula, variables):
    """
    Validate and evaluate a formula of the form:

        operand operator operand

    Example:
        x + 5
        10 / 2
        price * quantity
    """

    parts = formula.split()

    # The assignment specifies:
    # operand operator operand
    if len(parts) != 3:
        raise InvalidFormatError(
            "Formula must contain operand operator operand."
        )

    left_operand = parts[0]
    operator = parts[1]
    right_operand = parts[2]

    

    supported_operators = {
        "+",
        "-",
        "*",
        "/",
        "%"
    }

    if operator not in supported_operators:

        # Operators consisting of common operator characters are
        # still reported as unsupported rather than as operands.
        raise UnsupportedOperatorError(
            f"Unsupported operator: {operator}"
        )

    left = get_operand_value(
        left_operand,
        variables
    )

    right = get_operand_value(
        right_operand,
        variables
    )

    return calculate(
        left,
        operator,
        right
    )




def process_assignment(line, variables):
    """
    Process an assignment such as:

        x = 10

    or:

        x = 5.5
    """

    # Assignment must contain exactly one '='.
    if line.count("=") != 1:
        raise InvalidFormatError(
            "Invalid assignment format."
        )

    variable_name, value_text = line.split(
        "=",
        1
    )

    variable_name = variable_name.strip()
    value_text = value_text.strip()

    # Validate variable name.
    if not is_valid_variable_name(variable_name):
        raise InvalidFormatError(
            f"Invalid variable name: {variable_name}"
        )

    if not value_text:
        raise InvalidFormatError(
            "Assignment value cannot be empty."
        )

    
    value = get_operand_value(
        value_text,
        variables
    )

    variables[variable_name] = value

    return value




def format_result(value):
    """
    Format the result cleanly.

    Integer-valued floats are printed without unnecessary '.0'.
    """

    if isinstance(value, float):

        if value.is_integer():
            return str(int(value))

        return str(value)

    return str(value)




def process_line(line, variables):
    """
    Process one user command.

    Returns:
        None for assignments
        string result for formulas
        'QUIT' for quit
    """

    line = line.strip()

    if not line:
        raise InvalidFormatError(
            "Input cannot be empty."
        )

   
    if line.lower() == "quit":
        return "QUIT"

    
    if "=" in line:

        value = process_assignment(
            line,
            variables
        )

        # Assignments do not need to print a result unless
        # specified. The assignment's sample shows no output
        # for x = 10.
        return None

   
    result = evaluate_formula(
        line,
        variables
    )

    return format_result(result)



def main():
    """
    Interactive calculator.

    Continues until the user enters 'quit'.
    """

    variables = {}

    while True:

        try:

            line = input().strip()

            result = process_line(
                line,
                variables
            )

            if result == "QUIT":
                break

            if result is not None:
                print(result)

        except EOFError:
            # Gracefully terminate if input ends unexpectedly.
            break

        except FormulaError as error:

            # Print the custom exception name and message.
            print(
                f"{type(error).__name__}: {error}"
            )

        except (ValueError, OverflowError) as error:

            # Defensive handling for unexpected numeric errors.
            print(
                f"InvalidFormatError: {error}"
            )


if __name__ == "__main__":
    main()

"""
Programming with Python (202044504)
Assignment 1 - Question 7

Interactive Formula Validator with Custom Exceptions

Python Version: 3.10+
External Packages: None

Features:
    - Variable assignment
    - Integer operands
    - Decimal operands
    - Variable operands
    - +, -, *, / and % operators
    - Custom exceptions
    - Division-by-zero handling
    - Unsupported-operator handling
    - Invalid-format handling
    - Interactive execution until 'quit'
"""
