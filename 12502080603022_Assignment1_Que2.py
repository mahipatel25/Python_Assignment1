

from collections import deque


class AhoCorasick:
    """Aho-Corasick automaton for multi-pattern substring searching."""

    def __init__(self):
        # Each dictionary stores outgoing character transitions.
        self.children = [{}]

        # Failure link for every node.
        self.fail = [0]

        # True if a banned word ends at this node or through a
        # failure link.
        self.output = [False]

    def add_word(self, word):
        """Add one banned word to the trie."""

        word = word.lower()

        node = 0

        for character in word:
            if character not in self.children[node]:
                new_node = len(self.children)

                self.children[node][character] = new_node

                self.children.append({})
                self.fail.append(0)
                self.output.append(False)

            node = self.children[node][character]

        # A banned word ends at this node.
        self.output[node] = True

    def build_failure_links(self):
        """Build failure links using BFS."""

        queue = deque()

        # All children of root have failure link 0.
        for child in self.children[0].values():
            self.fail[child] = 0
            queue.append(child)

        while queue:
            current = queue.popleft()

            for character, child in self.children[current].items():

                queue.append(child)

                failure_node = self.fail[current]

                # Follow failure links until a matching transition
                # is found or the root is reached.
                while (
                    failure_node != 0
                    and character not in self.children[failure_node]
                ):
                    failure_node = self.fail[failure_node]

                self.fail[child] = self.children[failure_node].get(
                    character,
                    0
                )

                # If a banned word ends at the failure node, it also
                # means a banned word ends at the current node.
                if self.output[self.fail[child]]:
                    self.output[child] = True

    def contains_banned_word(self, text):
        """
        Return True if text contains any banned word.

        Searching is case-insensitive.
        """

        text = text.lower()
        node = 0

        for character in text:

            while (
                node != 0
                and character not in self.children[node]
            ):
                node = self.fail[node]

            node = self.children[node].get(character, 0)

            if self.output[node]:
                return True

        return False


def has_repeated_character(password):
    """
    Return True if any character occurs more than three
    consecutive times.
    """

    if len(password) < 4:
        return False

    consecutive_count = 1

    for index in range(1, len(password)):

        if password[index] == password[index - 1]:
            consecutive_count += 1

            if consecutive_count > 3:
                return True

        else:
            consecutive_count = 1

    return False


def satisfies_character_requirements(password):
    """
    Check lowercase, uppercase, digit and allowed special symbol
    requirements.
    """

    has_lowercase = False
    has_uppercase = False
    has_digit = False
    has_special = False

    for character in password:

        if character.islower():
            has_lowercase = True

        elif character.isupper():
            has_uppercase = True

        elif character.isdigit():
            has_digit = True

        elif character in "$#@":
            has_special = True

    return (
        has_lowercase
        and has_uppercase
        and has_digit
        and has_special
    )


def classify_password(password, automaton):
    """
    Classify one password.

    Priority:
        1. COMPROMISED
        2. WEAK_LENGTH
        3. WEAK_PATTERN
        4. STRONG

    A compromised password is reported as COMPROMISED even if it
    also violates another password rule.
    """

    # A banned dictionary word makes the password compromised.
    if automaton.contains_banned_word(password):
        return "COMPROMISED"

    # Password length must be between 6 and 12 inclusive.
    if not 6 <= len(password) <= 12:
        return "WEAK_LENGTH"

    # Check for more than three consecutive identical characters.
    if has_repeated_character(password):
        return "WEAK_PATTERN"

    # Check lowercase, uppercase, digit and special symbol.
    if not satisfies_character_requirements(password):
        return "WEAK_PATTERN"

    return "STRONG"


def process_input(data):
    """
    Process the complete input and return output lines.

    This function is separated from main() so the program can be
    tested easily without relying on interactive input.
    """

    lines = data.splitlines()

    if not lines:
        raise ValueError("Input cannot be empty.")

    current_line = 0

    # Read number of banned words.
    try:
        banned_count = int(lines[current_line].strip())
    except ValueError:
        raise ValueError("Number of banned words must be an integer.")

    current_line += 1

    if banned_count < 1 or banned_count > 10000:
        raise ValueError(
            "Number of banned words must be between 1 and 10000."
        )

    # Read banned words.
    banned_words = []

    for _ in range(banned_count):

        if current_line >= len(lines):
            raise ValueError("Missing banned word.")

        word = lines[current_line].strip()
        current_line += 1

        if not word:
            raise ValueError("Banned word cannot be empty.")

        banned_words.append(word)

    # Read number of passwords.
    if current_line >= len(lines):
        raise ValueError("Missing number of passwords.")

    try:
        password_count = int(lines[current_line].strip())
    except ValueError:
        raise ValueError(
            "Number of passwords must be an integer."
        )

    current_line += 1

    if password_count < 1 or password_count > 100000:
        raise ValueError(
            "Number of passwords must be between 1 and 100000."
        )

    if len(lines) - current_line < password_count:
        raise ValueError("Not enough passwords provided.")

    # Build the Aho-Corasick automaton once.
    automaton = AhoCorasick()

    for word in banned_words:
        automaton.add_word(word)

    automaton.build_failure_links()

    results = []

    # Classify every password.
    for index in range(1, password_count + 1):

        password = lines[current_line]
        current_line += 1

        classification = classify_password(
            password,
            automaton
        )

        results.append(
            f"{index}: {classification}"
        )

    return results


def main():
    """Read input from standard input and print the results."""

    try:
        # Using sys.stdin.read() allows the complete input to be
        # supplied at once.
        import sys

        data = sys.stdin.read()

        results = process_input(data)

        for result in results:
            print(result)

    except (ValueError, OSError) as error:
        print(f"INVALID INPUT: {error}")


if __name__ == "__main__":
    main()

"""
Programming with Python (202044504)
Assignment 1 - Question 2

Optimized Password Audit with Pattern Constraints

Python Version: 3.10+
External Packages: None

Algorithm:
    Aho-Corasick automaton is used to detect banned words efficiently.

Classification:
    COMPROMISED  -> contains a banned word
    WEAK_LENGTH  -> length is outside 6 to 12
    WEAK_PATTERN -> does not satisfy the required password pattern
                    or contains a character repeated more than 3 times
    STRONG       -> satisfies all requirements
"""
