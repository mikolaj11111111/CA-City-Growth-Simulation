from check_functions import *

def rule_res_low_expansion(grid, threshold=3):
    """
    Ekspansja Res Low: ≥threshold sąsiadów Res Low → Res Low
    """
    new_grid = grid.copy()
    neighbors = count_neighbors(grid, 1)
    
    can_change = (grid != 6) & (grid != 7) & (grid != 1)
    should_change = neighbors >= threshold
    
    new_grid[can_change & should_change] = 1
    return new_grid

def rule_high_density(grid, threshold=5):
    """
    Gęsta zabudowa: Empty z ≥threshold sąsiadów residential → Res High
    """
    new_grid = grid.copy()
    neighbors = count_neighbors_any(grid, [1, 2])  # Res Low + Res High
    
    can_change = (grid == 0)  # Tylko Empty
    should_change = neighbors >= threshold
    
    new_grid[can_change & should_change] = 2
    return new_grid

def rule_gentrification(grid, threshold=4):
    """
    Gentryfikacja: Res Low z ≥threshold sąsiadów Commercial → Commercial
    """
    new_grid = grid.copy()
    neighbors = count_neighbors(grid, 3)  # Commercial
    
    can_change = (grid == 1)  # Tylko Res Low
    should_change = neighbors >= threshold
    
    new_grid[can_change & should_change] = 3
    return new_grid

def rule_commercial_roads(grid, res_threshold=2):
    """
    Rozwój komercyjny: Empty obok Roads + ≥res_threshold sąsiadów residential → Commercial
    """
    new_grid = grid.copy()
    
    near_roads = is_near_type(grid, 7, max_distance=1)  # Obok dróg
    res_neighbors = count_neighbors_any(grid, [1, 2])
    
    can_change = (grid == 0)  # Tylko Empty
    should_change = near_roads & (res_neighbors >= res_threshold)
    
    new_grid[can_change & should_change] = 3
    return new_grid

def rule_suburban_sprawl(grid, center_distance=80):
    """
    Suburbanizacja: Empty daleko od centrum + ≥2 sąsiadów Res Low → Res Low
    """
    new_grid = grid.copy()
    
    distances = distance_from_center(grid)
    neighbors = count_neighbors(grid, 1)
    
    can_change = (grid == 0)  # Tylko Empty
    far_from_center = distances > center_distance
    should_change = far_from_center & (neighbors >= 2)
    
    new_grid[can_change & should_change] = 1
    return new_grid

def rule_park_pressure(grid, threshold=6):
    """
    Presja na parki: Parks z ≥threshold sąsiadów residential → Res Low
    """
    new_grid = grid.copy()
    neighbors = count_neighbors_any(grid, [1, 2])
    
    can_change = (grid == 5)  # Tylko Parks
    should_change = neighbors >= threshold
    
    new_grid[can_change & should_change] = 1
    return new_grid

def rule_industrial_periphery(grid):
    """
    Industrializacja: Empty daleko od centrum + blisko Roads → Industrial
    """
    new_grid = grid.copy()
    
    distances = distance_from_center(grid)
    near_roads = is_near_type(grid, 7, max_distance=2)
    
    can_change = (grid == 0)  # Tylko Empty
    far_from_center = distances > 70
    should_change = far_from_center & near_roads
    
    new_grid[can_change & should_change] = 4
    return new_grid

def rule_urban_decay(grid):
    """
    Degradacja: Commercial/Industrial z <2 sąsiadami residential → Empty
    """
    new_grid = grid.copy()
    neighbors = count_neighbors_any(grid, [1, 2])
    
    can_change = (grid == 3) | (grid == 4)  # Commercial lub Industrial
    should_change = neighbors < 2
    
    new_grid[can_change & should_change] = 0
    return new_grid
