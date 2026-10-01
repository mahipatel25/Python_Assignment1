import os
import sys
import re
import pickle
import zipfile
from collections import defaultdict


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def normalize_tokens(text):
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def build_index(folder_path, output_zip):
    if not os.path.isdir(folder_path):
        raise FileNotFoundError("Folder does not exist")

    index = defaultdict(list)
    files_processed = 0
    lines_processed = 0

    log_files = []

    for filename in sorted(os.listdir(folder_path)):
        file_path = os.path.join(folder_path, filename)

        if not os.path.isfile(file_path):
            continue

        if not filename.lower().endswith(".txt"):
            continue

        log_files.append(file_path)

    for file_path in log_files:
        filename = os.path.basename(file_path)
        files_processed += 1

        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            for line_number, line in enumerate(file, start=1):
                lines_processed += 1

                tokens = normalize_tokens(line)

                for token in set(tokens):
                    index[token].append((filename, line_number))

    index = dict(index)

    index_path = os.path.join(folder_path, "log_index.pkl")

    with open(index_path, "wb") as file:
        pickle.dump(index, file, protocol=pickle.HIGHEST_PROTOCOL)

    with zipfile.ZipFile(
        output_zip,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        for file_path in log_files:
            archive.write(
                file_path,
                arcname=os.path.basename(file_path)
            )

        archive.write(
            index_path,
            arcname="log_index.pkl"
        )

    os.remove(index_path)

    return files_processed, lines_processed, len(index)


def search_index(pickle_path, queries):
    if not os.path.isfile(pickle_path):
        raise FileNotFoundError("Pickle index file does not exist")

    with open(pickle_path, "rb") as file:
        index = pickle.load(file)

    results = []

    for query in queries:
        token = query.strip().lower()

        matches = index.get(token, [])

        if matches:
            output = " ".join(
                f"{filename}:{line_number}"
                for filename, line_number in matches
            )
            results.append(f"{token} {output}")
        else:
            results.append(f"{token} NOT_FOUND")

    return results


def process_input(data):
    lines = data.splitlines()

    if not lines:
        return ""

    operation = lines[0].strip().upper()

    try:
        if operation == "BUILD":
            if len(lines) < 3:
                return "INVALID INPUT"

            folder_path = lines[1].strip()
            output_zip = lines[2].strip()

            files, total_lines, tokens = build_index(
                folder_path,
                output_zip
            )

            return (
                f"FILES {files}\n"
                f"LINES {total_lines}\n"
                f"TOKENS {tokens}"
            )

        if operation == "SEARCH":
            if len(lines) < 3:
                return "INVALID INPUT"

            pickle_path = lines[1].strip()

            try:
                q = int(lines[2].strip())
            except ValueError:
                return "INVALID INPUT"

            if q < 0 or len(lines) < 3 + q:
                return "INVALID INPUT"

            queries = lines[3:3 + q]

            return "\n".join(
                search_index(pickle_path, queries)
            )

        return "INVALID INPUT"

    except (FileNotFoundError, PermissionError, OSError):
        return "FILE_ERROR"

    except (pickle.PickleError, EOFError, ValueError, TypeError):
        return "INVALID_INDEX"


def main():
    data = sys.stdin.read()
    output = process_input(data)

    if output:
        print(output)


if __name__ == "__main__":
    main()