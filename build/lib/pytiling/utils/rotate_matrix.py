def rotate_matrix(matrix, angle):
    if angle == 0:
        return matrix
    if angle == 90:
        return [list(row) for row in zip(*matrix[::-1])]
    elif angle == 180:
        return [row[::-1] for row in matrix[::-1]]
    elif angle == 270:
        return [list(row) for row in zip(*matrix)][::-1]
    else:
        raise ValueError("Angle must be one of 0, 90, 180, or 270")
