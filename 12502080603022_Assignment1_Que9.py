import sys
import threading
import heapq


class Job:
    def __init__(self, arrival, job_id, priority, duration, resources, order):
        self.arrival = arrival
        self.job_id = job_id
        self.priority = priority
        self.duration = duration
        self.resources = resources
        self.order = order


def schedule_jobs(workers, jobs):
    jobs.sort(key=lambda x: (x.arrival, x.order))

    available = []
    waiting = []
    results = []

    worker_available = [0] * workers
    worker_lock = threading.Lock()

    current_time = 0
    next_job = 0
    completed = 0

    while completed < len(jobs):
        while next_job < len(jobs) and jobs[next_job].arrival <= current_time:
            job = jobs[next_job]
            heapq.heappush(
                waiting,
                (-job.priority, job.arrival, job.order, job)
            )
            next_job += 1

        free_workers = [
            i for i in range(workers)
            if worker_available[i] <= current_time
        ]

        while waiting and free_workers:
            _, _, _, job = heapq.heappop(waiting)
            worker = free_workers.pop(0)

            start = max(current_time, job.arrival)
            finish = start + job.duration

            with worker_lock:
                worker_available[worker] = finish

            results.append(
                (
                    start,
                    job.job_id,
                    worker + 1,
                    finish,
                    start - job.arrival
                )
            )

            completed += 1

        if completed == len(jobs):
            break

        next_arrival = (
            jobs[next_job].arrival
            if next_job < len(jobs)
            else float("inf")
        )

        next_worker = min(worker_available)

        if waiting and next_worker > current_time:
            current_time = next_worker
        elif next_arrival > current_time:
            current_time = next_arrival
        else:
            current_time += 1

    results.sort(key=lambda x: (x[0], x[1]))

    return results


def process_input(data):
    lines = data.strip().splitlines()

    if not lines:
        return ""

    try:
        first = lines[0].split()

        if len(first) != 2:
            return "INVALID INPUT"

        workers = int(first[0])
        n = int(first[1])

        if workers <= 0 or n < 0:
            return "INVALID INPUT"

        if len(lines) != n + 1:
            return "INVALID INPUT"

        jobs = []

        for i in range(n):
            parts = lines[i + 1].split()

            if len(parts) != 5:
                return "INVALID INPUT"

            arrival = int(parts[0])
            job_id = parts[1]
            priority = int(parts[2])
            duration = int(parts[3])
            resources = int(parts[4])

            if arrival < 0 or duration < 0 or resources < 0:
                return "INVALID INPUT"

            jobs.append(
                Job(
                    arrival,
                    job_id,
                    priority,
                    duration,
                    resources,
                    i
                )
            )

        results = schedule_jobs(workers, jobs)

        output = []

        total_wait = 0

        for start, job_id, worker, finish, wait in results:
            output.append(
                f"{job_id} W{worker} {start} {finish}"
            )
            total_wait += wait

        if n > 0:
            average_wait = total_wait / n
        else:
            average_wait = 0.0

        output.append(f"AVG_WAIT {average_wait:.2f}")

        return "\n".join(output)

    except (ValueError, IndexError):
        return "INVALID INPUT"


def main():
    data = sys.stdin.read()
    result = process_input(data)

    if result:
        print(result)


if __name__ == "__main__":
    main()