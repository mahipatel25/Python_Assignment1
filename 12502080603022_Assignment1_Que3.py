


import re
import sys


# Signed 64-bit integer limits.
INT64_MIN = -(2 ** 63)
INT64_MAX = (2 ** 63) - 1

# Variable names follow normal identifier-style naming.
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_identifier(name):
    """Return True if name is a valid variable identifier."""
    return bool(IDENTIFIER_PATTERN.fullmatch(name))


def parse_expression(expression):
    """
    Convert an infix expression into Reverse Polish Notation (RPN).

    Supported operators:
        +
        -
        *

    Returns:
        List of tokens.

    Raises:
        ValueError if the expression is invalid.
    """

    tokens = []
    operators = []

    precedence = {
        "+": 1,
        "-": 1,
        "*": 2
    }

    # True means the parser is currently expecting an operand.
    expecting_operand = True

    index = 0
    length = len(expression)

    while index < length:

        character = expression[index]

        # Ignore whitespace.
        if character.isspace():
            index += 1
            continue

        # ---------------------------------------------------------
        # INTEGER
        # ---------------------------------------------------------
        if character.isdigit():

            if not expecting_operand:
                raise ValueError("Missing operator")

            start = index

            while (
                index < length
                and expression[index].isdigit()
            ):
                index += 1

            number_text = expression[start:index]
            number = int(number_text)

            # The problem specifies signed 64-bit values.
            if number > INT64_MAX:
                raise ValueError("Integer overflow")

            tokens.append(("NUMBER", number))
            expecting_operand = False
            continue

        # ---------------------------------------------------------
        # VARIABLE
        # ---------------------------------------------------------
        if character.isalpha() or character == "_":

            if not expecting_operand:
                raise ValueError("Missing operator")

            start = index
            index += 1

            while index < length:
                current = expression[index]

                if current.isalnum() or current == "_":
                    index += 1
                else:
                    break

            name = expression[start:index]

            if not is_valid_identifier(name):
                raise ValueError("Invalid variable name")

            tokens.append(("VARIABLE", name))
            expecting_operand = False
            continue

        # ---------------------------------------------------------
        # OPENING PARENTHESIS
        # ---------------------------------------------------------
        if character == "(":

            if not expecting_operand:
                raise ValueError("Invalid opening parenthesis")

            operators.append("(")
            index += 1
            continue

        # ---------------------------------------------------------
        # CLOSING PARENTHESIS
        # ---------------------------------------------------------
        if character == ")":

            if expecting_operand:
                raise ValueError("Invalid closing parenthesis")

            found_opening = False

            while operators:

                operator = operators.pop()

                if operator == "(":
                    found_opening = True
                    break

                tokens.append(("OPERATOR", operator))

            if not found_opening:
                raise ValueError("Unmatched parenthesis")

            index += 1
            continue

        # ---------------------------------------------------------
        # OPERATOR
        # ---------------------------------------------------------
        if character in "+-*":

            # Unary operators are not part of the problem.
            if expecting_operand:
                raise ValueError("Invalid operator position")

            while (
                operators
                and operators[-1] != "("
                and precedence[operators[-1]]
                >= precedence[character]
            ):
                tokens.append(
                    ("OPERATOR", operators.pop())
                )

            operators.append(character)

            expecting_operand = True
            index += 1
            continue

        # Any other character is invalid.
        raise ValueError("Invalid character")

    # An expression cannot finish while waiting for an operand.
    if expecting_operand:
        raise ValueError("Incomplete expression")

    # Remove remaining operators.
    while operators:

        operator = operators.pop()

        if operator == "(":
            raise ValueError("Unmatched opening parenthesis")

        tokens.append(("OPERATOR", operator))

    return tokens


def parse_definition(line):
    """
    Parse a variable definition of the form:

        variable = expression

    Returns:
        (variable_name, parsed_expression)
    """

    # Exactly one '=' is required.
    if line.count("=") != 1:
        raise ValueError("Invalid assignment")

    variable_name, expression = line.split("=", 1)

    variable_name = variable_name.strip()
    expression = expression.strip()

    if not is_valid_identifier(variable_name):
        raise ValueError("Invalid variable name")

    if not expression:
        raise ValueError("Missing expression")

    parsed_expression = parse_expression(expression)

    return variable_name, parsed_expression


def calculate_operation(left, operator, right):
    """
    Perform one arithmetic operation and verify signed 64-bit range.
    """

    if operator == "+":
        result = left + right

    elif operator == "-":
        result = left - right

    elif operator == "*":
        result = left * right

    else:
        raise ValueError("Invalid operator")

    if result < INT64_MIN or result > INT64_MAX:
        raise ValueError("Integer overflow")

    return result


def evaluate_expressions(definitions, final_expression):
    """
    Evaluate the final expression.

    Uses:
        - memoization
        - cycle detection
        - explicit stack

    This simulates recursive evaluation without relying on Python's
    recursion limit.
    """

    # -------------------------------------------------------------
    # Parse the final expression.
    # -------------------------------------------------------------
    final_tokens = parse_expression(final_expression)

    # -------------------------------------------------------------
    # memo:
    # variable -> already calculated value
    # -------------------------------------------------------------
    memo = {}

    # -------------------------------------------------------------
    # state:
    #
    # 1 = currently being evaluated
    # 2 = completely evaluated
    # -------------------------------------------------------------
    state = {}

    # -------------------------------------------------------------
    # Each frame represents one expression currently being evaluated.
    #
    # tokens  -> RPN tokens
    # position -> current token position
    # values -> evaluation stack
    # variable -> variable whose expression is being evaluated
    # -------------------------------------------------------------
    evaluation_stack = [
        {
            "tokens": final_tokens,
            "position": 0,
            "values": [],
            "variable": None
        }
    ]

    while evaluation_stack:

        frame = evaluation_stack[-1]

        tokens = frame["tokens"]
        position = frame["position"]

        # ---------------------------------------------------------
        # Current expression is completely evaluated.
        # ---------------------------------------------------------
        if position >= len(tokens):

            if len(frame["values"]) != 1:
                raise ValueError("Invalid expression")

            result = frame["values"][0]

            if result < INT64_MIN or result > INT64_MAX:
                raise ValueError("Integer overflow")

            completed_variable = frame["variable"]

            evaluation_stack.pop()

            # Store calculated variable in memoization dictionary.
            if completed_variable is not None:

                memo[completed_variable] = result
                state[completed_variable] = 2

            # Return result to the previous expression.
            if evaluation_stack:

                evaluation_stack[-1]["values"].append(result)

            else:

                return result

            continue

        # Get the next RPN token.
        token_type, token_value = tokens[position]

        frame["position"] += 1

        # ---------------------------------------------------------
        # NUMBER
        # ---------------------------------------------------------
        if token_type == "NUMBER":

            frame["values"].append(token_value)

        # ---------------------------------------------------------
        # VARIABLE
        # ---------------------------------------------------------
        elif token_type == "VARIABLE":

            variable_name = token_value

            # Variable must have a definition.
            if variable_name not in definitions:
                raise ValueError("Unknown variable")

            # If already calculated, use memoized value.
            if variable_name in memo:

                frame["values"].append(
                    memo[variable_name]
                )

            # If currently being evaluated, we found a cycle.
            elif state.get(variable_name) == 1:

                raise RuntimeError("CYCLE")

            else:

                # Mark variable as currently being evaluated.
                state[variable_name] = 1

                # Start evaluating its expression.
                evaluation_stack.append(
                    {
                        "tokens": definitions[variable_name],
                        "position": 0,
                        "values": [],
                        "variable": variable_name
                    }
                )

        # ---------------------------------------------------------
        # OPERATOR
        # ---------------------------------------------------------
        elif token_type == "OPERATOR":

            if len(frame["values"]) < 2:
                raise ValueError("Invalid expression")

            right = frame["values"].pop()
            left = frame["values"].pop()

            result = calculate_operation(
                left,
                token_value,
                right
            )

            frame["values"].append(result)

        else:

            raise ValueError("Invalid token")

    raise ValueError("Evaluation failed")


def process_input(data):
    """
    Process the complete input string.

    This function is intentionally separated from main() so that
    the program can be tested without requiring interactive input.
    """

    lines = data.splitlines()

    if not lines:
        return "INVALID"

    # -------------------------------------------------------------
    # Number of variables.
    # -------------------------------------------------------------
    try:
        variable_count = int(lines[0].strip())
    except ValueError:
        return "INVALID"

    if not (1 <= variable_count <= 200000):
        return "INVALID"

    # We need:
    #   1 line for n
    #   n definition lines
    #   1 final expression
    if len(lines) < variable_count + 2:
        return "INVALID"

    definitions = {}

    try:

        # ---------------------------------------------------------
        # Read variable definitions.
        # ---------------------------------------------------------
        for index in range(1, variable_count + 1):

            line = lines[index].strip()

            if not line:
                return "INVALID"

            name, parsed_expression = parse_definition(line)

            # Duplicate variable definitions are invalid.
            if name in definitions:
                return "INVALID"

            definitions[name] = parsed_expression

        # ---------------------------------------------------------
        # Last line is the expression to evaluate.
        # ---------------------------------------------------------
        final_expression = lines[variable_count + 1].strip()

        if not final_expression:
            return "INVALID"

        return str(
            evaluate_expressions(
                definitions,
                final_expression
            )
        )

    except RuntimeError as error:

        if str(error) == "CYCLE":
            return "CYCLE"

        return "INVALID"

    except (ValueError, OverflowError):

        return "INVALID"


def main():
    """Read input and print the required result."""

    try:

        data = sys.stdin.read()

        if not data.strip():
            print("INVALID")
            return

        print(process_input(data))

    except OSError:
        print("INVALID")


if __name__ == "__main__":
    main()

"""
Programming with Python (202044504)
Assignment 1 - Question 3

Recursive Expression Engine with Memoization

Python Version: 3.10+
External Packages: None

Supported:
    Non-negative integers
    Variables
    +
    -
    *
    Parentheses

Output:
    Integer result
    CYCLE  -> cyclic variable dependency
    INVALID -> invalid expression/input

The evaluator uses:
    - Shunting-yard parsing
    - Reverse Polish Notation (RPN)
    - Memoization
    - Explicit stack-based recursive evaluation
      to avoid Python recursion-depth errors
"""