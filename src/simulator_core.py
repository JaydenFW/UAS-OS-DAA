# src/simulator_core.py
import time
from copy import deepcopy
from banker import count_need

def _matrix_copy(mat):
    return [row[:] for row in mat]

def run_standard_with_steps(allocation, max_mat, available):
    """
    Runs standard banker and returns:
      - steps: list of dicts {t, allocation, max, need, available, executed, comparisons_so_far}
      - metrics: {total_comparisons, total_iterations, elapsed_time}
      - safe_seq (or None)
    """
    start = time.perf_counter()
    alloc = _matrix_copy(allocation)
    maxm = _matrix_copy(max_mat)
    avail = available[:]
    need = count_need(alloc, maxm)

    M = len(alloc)
    N = len(avail)

    finish = [False] * M
    safe_seq = []
    steps = []
    total_comparisons = 0
    iteration = 0
    changed = True

    while changed:
        changed = False
        iteration += 1
        # snapshot before iteration
        steps.append({
            "t": f"T{iteration-1}",
            "allocation": _matrix_copy(alloc),
            "max": _matrix_copy(maxm),
            "need": _matrix_copy(need),
            "available": avail[:],
            "executed": None,
            "comparisons_so_far": total_comparisons
        })

        for i in range(M):
            if not finish[i]:
                # check need <= available (count comparisons)
                comp_count = 0
                can_run = True
                for j in range(N):
                    comp_count += 1
                    if need[i][j] > avail[j]:
                        can_run = False
                total_comparisons += comp_count

                if can_run:
                    # execute process i
                    for j in range(N):
                        avail[j] += alloc[i][j]
                    finish[i] = True
                    safe_seq.append(i)
                    changed = True
                    # log a step showing execution
                    steps.append({
                        "t": f"T{iteration-1}.exec",
                        "allocation": _matrix_copy(alloc),
                        "max": _matrix_copy(maxm),
                        "need": _matrix_copy(need),
                        "available": avail[:],
                        "executed": i,
                        "comparisons_so_far": total_comparisons
                    })
    elapsed = time.perf_counter() - start
    metrics = {
        "total_comparisons": total_comparisons,
        "total_iterations": iteration,
        "elapsed_time": elapsed
    }
    if all(finish):
        return steps, metrics, safe_seq
    else:
        return steps, metrics, None


def run_dynamic_with_steps(allocation, max_mat, available, arrival_schedule):
    """
    arrival_schedule: dict mapping integer iteration (T index) -> list of max vectors to arrive at that T
      e.g. {1: [[4,3,3]], 3: [[2,1,1], [1,1,1]]}
    Returns steps, metrics, safe_seq_or_None
    """

    start = time.perf_counter()
    alloc = _matrix_copy(allocation)
    maxm = _matrix_copy(max_mat)
    avail = available[:]
    need = count_need(alloc, maxm)

    M = len(alloc)
    N = len(avail)

    finish = [False] * M
    safe_seq = []
    steps = []
    total_comparisons = 0
    iteration = 0

    # We'll treat iteration numbers same as standard (iteration increases each outer loop)
    loop_stuck = False
    # We'll allow arrivals at the start of iteration T_k (before searching)
    while False in finish and not loop_stuck:
        # check arrivals at this iteration index
        arrivals = arrival_schedule.get(iteration, [])
        if arrivals:
            for vec in arrivals:
                alloc.append([0] * N)
                maxm.append(vec)
                finish.append(False)
            need = count_need(alloc, maxm)
            M = len(alloc)
            # log arrival snapshot
            steps.append({
                "t": f"T{iteration}.arrival",
                "allocation": _matrix_copy(alloc),
                "max": _matrix_copy(maxm),
                "need": _matrix_copy(need),
                "available": avail[:],
                "executed": None,
                "arrivals": arrivals,
                "comparisons_so_far": total_comparisons
            })
            # mark possible stuck to detect unsafe if cannot proceed
            loop_stuck = True

        # snapshot before searching for executable processes
        steps.append({
            "t": f"T{iteration}",
            "allocation": _matrix_copy(alloc),
            "max": _matrix_copy(maxm),
            "need": _matrix_copy(need),
            "available": avail[:],
            "executed": None,
            "comparisons_so_far": total_comparisons
        })

        loop_stuck = True
        progressed = False
        # Try to find any process to run
        for i in range(M):
            if not finish[i]:
                comp_count = 0
                can_run = True
                for j in range(N):
                    comp_count += 1
                    if need[i][j] > avail[j]:
                        can_run = False
                total_comparisons += comp_count

                if can_run:
                    # execute process i
                    for j in range(N):
                        avail[j] += alloc[i][j]
                    finish[i] = True
                    safe_seq.append(i)
                    progressed = True
                    loop_stuck = False
                    # log execution
                    steps.append({
                        "t": f"T{iteration}.exec",
                        "allocation": _matrix_copy(alloc),
                        "max": _matrix_copy(maxm),
                        "need": _matrix_copy(need),
                        "available": avail[:],
                        "executed": i,
                        "comparisons_so_far": total_comparisons
                    })
        iteration += 1
        # safety: if we finished all, break
        if all(finish):
            break

    elapsed = time.perf_counter() - start
    metrics = {
        "total_comparisons": total_comparisons,
        "total_iterations": iteration,
        "elapsed_time": elapsed
    }
    if loop_stuck:
        return steps, metrics, None
    return steps, metrics, safe_seq
