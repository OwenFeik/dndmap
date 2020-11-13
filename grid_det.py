import numpy as np

import image

def load_as_greyscale(path):
    """load specified path as a greyscale image"""
    return image.Image.from_file(path).as_greyscale_array()

def get_row_col_stddev(img):
    """return vectors of standard deviations of value for a greyscale image"""
    rows = [np.std(row) for row in img]
    cols = [np.std(img[:,j]) for j in range(len(img[0]))]

    return rows, cols

def get_row_deltas(rows, k=3):
    """
    given an input array rows which is a vector of standard deviations of
    image rows, return a dictionary which maps distances between rows
    which satisfy the condition of being k standard deviations away
    from the average of the last 15 rows to frequency of this distance.
    """ 
    
    prev = rows[:15] # the past 15 rows
    indexs = []
    for i, r in enumerate(rows):
        prev.append(r)
        prev = prev[1:]
        
        if abs(np.mean(prev) - r) > np.std(prev) * k:
            indexs.append(i)

    deltas = {}
    for i in range(len(indexs) - 1):
        d = indexs[i + 1] - indexs[i]
        if not d in deltas:
            deltas[d] = 0
        deltas[d] += 1

    return deltas

def pick_grid_size(deltas, d=20):
    """select grid size from delta dictionary"""

    # count multiples of a given delta (> d) as entries for that delta
    copy = deltas.copy()
    for delta in deltas:
        for other in deltas:
            if delta > d and other != delta and not other % delta:
                copy[delta] += other / delta
    deltas = copy

    return max(deltas, key=lambda k: deltas[k] * k)

def calc_grid_size(path):
    img = load_as_greyscale(path)
    rows, cols = get_row_col_stddev(img)
    row_size = pick_grid_size(get_row_deltas(rows))
    col_size = pick_grid_size(get_row_deltas(cols))

    print(row_size, col_size)

    if row_size != col_size:
        raise ValueError('Failed to determine a size for this grid.')

    return row_size

if __name__ == '__main__':
    import sys
    print(calc_grid_size(sys.argv[1]))
