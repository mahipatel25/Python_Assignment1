import heapq
import sys


def build_graph(module_names, import_pairs):
    

    graph = {
        module: []
        for module in module_names
    }

    indegree = {
        module: 0
        for module in module_names
    }

    # Sets are used to ignore duplicate import edges.
    seen_edges = set()

    for importer, dependency in import_pairs:

        # Every referenced module should belong to the supplied
        # module set.
        if (
            importer not in graph
            or dependency not in graph
        ):
            raise ValueError(
                "Import relationship contains unknown module."
            )

        # Ignore duplicate relationships.
        edge = (dependency, importer)

        if edge in seen_edges:
            continue

        seen_edges.add(edge)

        # dependency must be loaded before importer.
        graph[dependency].append(importer)

        indegree[importer] += 1

    return graph, indegree




def topological_sort(graph, indegree):
   
    current_indegree = dict(indegree)

    heap = []

    for module in current_indegree:

        if current_indegree[module] == 0:
            heapq.heappush(heap, module)

    order = []

    while heap:

        module = heapq.heappop(heap)

        order.append(module)

        for dependent in graph[module]:

            current_indegree[dependent] -= 1

            if current_indegree[dependent] == 0:
                heapq.heappush(
                    heap,
                    dependent
                )

    
    remaining = [
        module
        for module in current_indegree
        if current_indegree[module] > 0
    ]

    return order, remaining



def find_cycle(graph, remaining_modules):
    

    remaining = set(remaining_modules)

   
    state = {
        module: 0
        for module in remaining
    }

    # parent[module] stores the previous node in the DFS path.
    parent = {}

    for start in sorted(remaining):

        if state[start] != 0:
            continue

        # Stack entries:
        # (node, next-neighbor-index)
        stack = [(start, 0)]

        state[start] = 1
        parent[start] = None

        while stack:

            node, next_index = stack[-1]

            # Get only neighbors that can still be involved in
            # the cyclic portion.
            neighbors = [
                neighbor
                for neighbor in graph[node]
                if neighbor in remaining
            ]

            
            if next_index >= len(neighbors):

                state[node] = 2
                stack.pop()
                continue

            # Move to the next neighbor.
            neighbor = neighbors[next_index]

            stack[-1] = (
                node,
                next_index + 1
            )

            
            if state[neighbor] == 1:

                cycle = [neighbor]

                current = node

                while current != neighbor:

                    cycle.append(current)

                    current = parent[current]

                    if current is None:
                        # Defensive fallback.
                        return [neighbor, node, neighbor]

                cycle.append(neighbor)

                cycle.reverse()

                return cycle

            
            if state[neighbor] == 0:

                parent[neighbor] = node
                state[neighbor] = 1

                stack.append(
                    (neighbor, 0)
                )

    # This should not normally happen if remaining_modules
    # genuinely contains a cycle.
    return []




def process_input(data):
    """
    Process the complete input.

    Returns:
        List of output lines.
    """

    lines = [
        line.strip()
        for line in data.splitlines()
        if line.strip()
    ]

    if not lines:
        raise ValueError("Input is empty.")

    position = 0

    

    first = lines[position].split()
    position += 1

    if len(first) != 2:
        raise ValueError(
            "First line must contain n and e."
        )

    try:
        n = int(first[0])
        e = int(first[1])
    except ValueError:
        raise ValueError(
            "n and e must be integers."
        )

    if not (1 <= n <= 200000):
        raise ValueError(
            "Number of modules must be between 1 and 200000."
        )

    if not (0 <= e <= 500000):
        raise ValueError(
            "Number of edges must be between 0 and 500000."
        )

    

    if len(lines) - position < n:
        raise ValueError(
            "Not enough module names."
        )

    modules = []

    for _ in range(n):

        module = lines[position]
        position += 1

        if not module:
            raise ValueError(
                "Module name cannot be empty."
            )

        modules.append(module)

    # Module names must be unique.
    if len(set(modules)) != n:
        raise ValueError(
            "Duplicate module name found."
        )

   
    if len(lines) - position < e:
        raise ValueError(
            "Not enough import relationships."
        )

    import_pairs = []

    for _ in range(e):

        parts = lines[position].split()
        position += 1

        if len(parts) != 2:
            raise ValueError(
                "Each import relationship must contain two modules."
            )

        importer = parts[0]
        dependency = parts[1]

        import_pairs.append(
            (importer, dependency)
        )

   

    graph, indegree = build_graph(
        modules,
        import_pairs
    )

   
    order, remaining = topological_sort(
        graph,
        indegree
    )

   

    if not remaining:

        return [
            " ".join(order)
        ]

  
    cycle = find_cycle(
        graph,
        remaining
    )

    output = [
        "CYCLE"
    ]

    if cycle:
        output.append(
            " ".join(cycle)
        )

    return output




def main():
    """Read standard input and print the result."""

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
Assignment 1 - Question 6

Python Module Dependency Resolver

Python Version: 3.10+
External Packages: None

Features:
    - Topological sorting
    - Lexicographically smallest valid order
    - Duplicate edge removal
    - Cycle detection
    - One detected cycle is reported
    - Handles large graphs efficiently
"""