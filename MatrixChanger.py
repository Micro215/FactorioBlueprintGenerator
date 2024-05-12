def MatrixChanger(data: list, height: int, width: int) -> list:
    
    new_data = []

    for b in range(width):
        new_data.append([])
        for a in range(height):
            new_data[b].append(0)
    
    for a in range(height):
        for b in range(width):
            new_data[b][a] = data[a][b]

    return new_data


if __name__ == "__main__":
    data = [[1, 2, 3], [1, 2, 3],[1, 2, 3]]
    height = 3
    width = 3

    print(MatrixChanger(data, height, width))