def bead_sort(arr: list) -> list:
    num_elements = len(arr)
    if num_elements == 0:
        return arr

    # throw error with negative number
    if any(num < 0 for num in arr):
        raise ValueError("Bead sort does not support negative number")

    max_val = max(arr)

    # try to create grid 2D array
    beads = [[0] * max_val for i in range(num_elements)]

    # step 1: drop breads
    for i, element_value in enumerate(arr):
        for j in range(element_value):
            beads[i][j] = 1

    # step 2: bread fall down
    for j in range(max_val):
        sum = 0

        for i in range(num_elements):
            sum += beads[i][j]
            beads[i][j] = 0

        for i in range(num_elements - sum, num_elements):
            beads[i][j] = 1

    # step 3: read sorted value
    for i in range(num_elements):
        count = 0

        for j in range(max_val):
            count += beads[i][j]

        arr[i] = count

    return arr
