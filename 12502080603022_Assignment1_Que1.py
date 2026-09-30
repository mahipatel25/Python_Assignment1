

from decimal import Decimal, InvalidOperation


def validate_first_line(parts):
    """Validate and return n, k and m."""
    if len(parts) != 3:
        raise ValueError("First line must contain n, k and m.")

    try:
        n, k, m = map(int, parts)
    except ValueError:
        raise ValueError("n, k and m must be integers.")

    if not (1 <= n <= 100000):
        raise ValueError("n must be between 1 and 100000.")

    if not (1 <= k <= 50):
        raise ValueError("k must be between 1 and 50.")

    if not (1 <= m <= 12):
        raise ValueError("m must be between 1 and 12.")

    return n, k, m


def parse_student_record(line, m):
    """
    Parse and validate one student record.

    Returns:
        tuple: (enrollment, name, semester, cpi, marks)
    """
    parts = line.split()

    # 4 fixed fields + m subject marks
    if len(parts) != 4 + m:
        raise ValueError(
            f"Each student record must contain {4 + m} values."
        )

    enrollment = parts[0]
    name = parts[1]

    # Validate semester
    try:
        semester = int(parts[2])
    except ValueError:
        raise ValueError("Semester must be an integer.")

    if not (1 <= semester <= 8):
        raise ValueError("Semester must be between 1 and 8.")

    # Decimal avoids unnecessary floating-point comparison issues.
    try:
        cpi = Decimal(parts[3])
    except InvalidOperation:
        raise ValueError("CPI must be a valid number.")

    if not (Decimal("0.0") <= cpi <= Decimal("10.0")):
        raise ValueError("CPI must be between 0.0 and 10.0.")

    # Store marks as a tuple as required by the problem.
    marks = []

    for value in parts[4:]:
        try:
            mark = int(value)
        except ValueError:
            raise ValueError("Subject marks must be integers.")

        if not (0 <= mark <= 100):
            raise ValueError("Each mark must be between 0 and 100.")

        marks.append(mark)

    return enrollment, name, semester, cpi, tuple(marks)


def rank_students(students, k):
    """
    Return the top K students according to:
        1. Higher CPI
        2. Higher total marks (equivalent to higher average marks
           because every student has the same number of subjects)
        3. Lexicographically smaller enrollment number
    """

    ranked = sorted(
        students,
        key=lambda student: (
            -student[3],              # Higher CPI first
            -sum(student[4]),         # Higher average marks first
            student[0]                # Smaller enrollment first
        )
    )

    return ranked[:k]


def find_subject_toppers(students, m):
    """
    Find all students having the highest mark in each subject.

    Returns:
        list of lists containing enrollment numbers.
    """

    # Highest mark found for each subject.
    highest_marks = [-1] * m

    # Enrollment numbers of students achieving that highest mark.
    toppers = [[] for _ in range(m)]

    for student in students:
        enrollment = student[0]
        marks = student[4]

        for subject_index in range(m):
            mark = marks[subject_index]

            if mark > highest_marks[subject_index]:
                # New highest mark found.
                highest_marks[subject_index] = mark
                toppers[subject_index] = [enrollment]

            elif mark == highest_marks[subject_index]:
                # Another student has the same highest mark.
                toppers[subject_index].append(enrollment)

    # Sort tied enrollment numbers lexicographically.
    for subject_index in range(m):
        toppers[subject_index].sort()

    return toppers


def analyze_students(n, k, m, students):
    """
    Group students by semester, generate semester rankings,
    and find subject-wise toppers.
    """

    # Dictionary:
    # semester -> list of student records
    students_by_semester = {}

    for student in students:
        semester = student[2]

        if semester not in students_by_semester:
            students_by_semester[semester] = []

        students_by_semester[semester].append(student)

    output = []

    # Process semesters in ascending order.
    for semester in sorted(students_by_semester):
        top_students = rank_students(
            students_by_semester[semester],
            k
        )

        enrollments = [student[0] for student in top_students]

        output.append(
            f"Semester {semester}: {' '.join(enrollments)}"
        )

    # Find subject-wise toppers.
    subject_toppers = find_subject_toppers(students, m)

    for subject_index in range(m):
        enrollment_list = subject_toppers[subject_index]

        output.append(
            f"S{subject_index + 1}: {' '.join(enrollment_list)}"
        )

    return output


def main():
    """Main function to read input, process records and print output."""

    try:
        # Read first line.
        first_line = input().split()

        n, k, m = validate_first_line(first_line)

        # List of tuples containing student records.
        students = []

        for _ in range(n):
            line = input().strip()

            if not line:
                raise ValueError("Student record cannot be empty.")

            student = parse_student_record(line, m)
            students.append(student)

        result = analyze_students(n, k, m, students)

        for line in result:
            print(line)

    except (ValueError, EOFError) as error:
        print(f"INVALID INPUT: {error}")


if __name__ == "__main__":
    main()

"""
Programming with Python (202044504)
Assignment 1 - Question 1

Campus Merit Analyzer using Compound Data Structures

Python Version: 3.10+
External Packages: None

Input:
    First line: n k m
    Next n lines:
        enrollment name semester cpi mark1 mark2 ... markm

Output:
    Semester-wise top K students
    Subject-wise toppers
"""
