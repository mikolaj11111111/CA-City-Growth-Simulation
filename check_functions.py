from scipy.ndimage import convolve
import numpy as np



def count_neighbors(grid, value):
    """Liczy sąsiadów o określonej wartości (Moore)"""
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]])
    mask = (grid == value).astype(int)
    neighbors = convolve(mask, kernel, mode='constant', cval=0)
    return neighbors

def count_neighbors_any(grid, values):
    """Liczy sąsiadów o dowolnej wartości z listy"""
    total = np.zeros_like(grid)
    for value in values:
        total += count_neighbors(grid, value)
    return total

def is_near_type(grid, target_type, max_distance=3):
    """Sprawdza czy komórka jest blisko określonego typu (w promieniu max_distance)"""
    from scipy.ndimage import binary_dilation
    mask = (grid == target_type)
    for _ in range(max_distance):
        mask = binary_dilation(mask)
    return mask

def distance_from_center(grid):
    """Oblicza dystans każdej komórki od centrum gridu"""
    rows, cols = grid.shape
    center_row, center_col = rows // 2, cols // 2
    
    row_indices, col_indices = np.ogrid[:rows, :cols]
    distances = np.sqrt((row_indices - center_row)**2 + (col_indices - center_col)**2)
    return distances
