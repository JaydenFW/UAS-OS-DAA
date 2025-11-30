def count_need(allocation, max_mat):
    M = len(allocation)
    N = len(allocation[0])
    need = [[0]*N for _ in range(M)]
    for i in range(M):
        for j in range(N):
            need[i][j] = max_mat[i][j] - allocation[i][j]
    return need


def is_safe_sequence(allocation, max_mat, available):
    need = count_need(allocation, max_mat)
    M = len(allocation)
    N = len(available)

    finish = [False] * M
    work = available[:]  # copy
    safe_seq = []

    changed = True
    while changed:
        changed = False
        for i in range(M):
            if not finish[i]:
                if all(need[i][j] <= work[j] for j in range(N)):
                    for j in range(N):
                        work[j] += allocation[i][j]
                    finish[i] = True
                    safe_seq.append(i)
                    changed = True

    if all(finish):
        return safe_seq
    else:
        return None

