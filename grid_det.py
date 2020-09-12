import cv2
import numpy as np

i = cv2.imread('map.jpg')
i = cv2.cvtColor(i, cv2.COLOR_BGR2GRAY)

rows = [np.std(row) for row in i]
cols = [np.std(i[:,j]) for j in range(len(i))]

def calc_avg_delta(rows):
    prev = []
    indexs = []
    for i, r in enumerate(rows):
        prev.append(r)
        if len(prev) <= 15:
            continue
        prev = prev[1:]
        
        # print(abs(np.mean(prev)) - r)
        if abs(np.mean(prev) - r) > np.std(prev) * 2 + 1:
            print(i, r, abs(np.mean(prev) - r), np.std(prev) * 2 + 1)
            indexs.append(i)

    deltas = {}
    for i in range(len(indexs) - 1):
        if not indexs[i + 1] - indexs[i] in deltas:
            deltas[indexs[i + 1] - indexs[i]] = 0
        deltas[indexs[i + 1] - indexs[i]] += 1

    return max(deltas, key=lambda k: deltas[k])

print(calc_avg_delta(rows))
print(calc_avg_delta(cols))
