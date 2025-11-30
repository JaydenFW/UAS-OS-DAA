from src.banker import count_need


def dynamic_banker_loop(allocation, max_mat, available, new_requests_generator):
    need = count_need(allocation, max_mat)
    M = len(allocation)
    N = len(available)

    finish = [False] * M
    safe_seq = []
    loopWillStuck = False

    while False in finish and not loopWillStuck:
        # check for new request
        req = next(new_requests_generator, None)
        if req is not None:
            # append new process
            allocation.append([0] * N)
            max_mat.append(req)
            need = count_need(allocation, max_mat)
            finish.append(False)
            M += 1
            loopWillStuck = True

        loopWillStuck = True
        for i in range(M):
            if not finish[i]:
                if all(need[i][j] <= available[j] for j in range(N)):
                    safe_seq.append(i)
                    for j in range(N):
                        available[j] += allocation[i][j]
                    finish[i] = True
                    loopWillStuck = False

    if loopWillStuck:
        return None

    return safe_seq
