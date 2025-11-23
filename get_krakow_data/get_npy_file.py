import osmnx as ox
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from scipy.ndimage import binary_dilation, binary_closing, binary_opening, binary_fill_holes
from sklearn.cluster import DBSCAN

ox.settings.timeout = 600
ox.settings.use_cache = True

print("🔄 Pobieranie danych dla Krakowa...\n")

#center_point = (50.0619, 19.9369)
adress = 'Kraków, Poland'
distance = 4000

# ============================================
# POBIERANIE
# ============================================

try:
    buildings = ox.features_from_place(adress, tags={'building': True})
    print(f"✅ Budynki: {len(buildings)}")
except:
    buildings = None
    exit()

try:
    roads = ox.features_from_place(adress, tags={'highway': True})
    print(f"✅ Drogi: {len(roads)}")
except:
    roads = None

try:
    parks = ox.features_from_place(adress, tags={'leisure': ['park', 'garden'], 'landuse': 'forest'})
    print(f"✅ Parki: {len(parks)}")
except:
    parks = None

try:
    water = ox.features_from_place(adress, tags={'waterway': 'river', 'natural': 'water'})
    print(f"✅ Woda: {len(water)}")
except:
    water = None

print()

# ============================================
# BBOX & GRID
# ============================================

bounds = buildings.total_bounds
minx, miny, maxx, maxy = bounds

grid_size = 256
grid = np.zeros((grid_size, grid_size), dtype=int)

cell_width = (maxx - minx) / grid_size
cell_height = (maxy - miny) / grid_size

print(f"📐 Obszar: {(maxx-minx)*111:.2f}km × {(maxy-miny)*111:.2f}km")
print(f"🔲 Komórka: {cell_width*111*1000:.0f}m\n")

def point_to_grid(lon, lat):
    if lon < minx or lon > maxx or lat < miny or lat > maxy:
        return None, None
    col = int((lon - minx) / cell_width)
    row = int((maxy - lat) / cell_height)
    col = min(max(col, 0), grid_size - 1)
    row = min(max(row, 0), grid_size - 1)
    return row, col

# ============================================
# BUDYNKI - zbierz współrzędne i typy
# ============================================

print("🏘️  Przetwarzanie budynków...\n")

center_lon = (minx + maxx) / 2
center_lat = (miny + maxy) / 2

# Listy budynków według typu
res_low_points = []
res_high_points = []
commercial_points = []
industrial_points = []

for idx, feature in buildings.iterrows():
    try:
        geom = feature.geometry
        if geom.geom_type != 'Polygon':
            continue
        
        centroid = geom.centroid
        lon, lat = centroid.x, centroid.y
        
        row, col = point_to_grid(lon, lat)
        if row is None:
            continue
        
        dist_km = np.sqrt((lon - center_lon)**2 + (lat - center_lat)**2) * 111
        building_type = str(feature.get('building', 'yes')).lower()
        
        # Klasyfikuj
        if any(x in building_type for x in ['commercial', 'retail', 'shop']):
            commercial_points.append([row, col])
        elif any(x in building_type for x in ['industrial', 'warehouse']):
            industrial_points.append([row, col])
        elif dist_km < 0.5:
            res_high_points.append([row, col])
        else:
            res_low_points.append([row, col])
    except:
        pass

print(f"   Res Low:     {len(res_low_points)}")
print(f"   Res High:    {len(res_high_points)}")
print(f"   Commercial:  {len(commercial_points)}")
print(f"   Industrial:  {len(industrial_points)}")
print()

# ============================================
# CLUSTERYZACJA + WYPEŁNIANIE
# ============================================

def create_clustered_mask(points, grid_size, eps=3, min_samples=5):
    """
    Clusteryzuje punkty i wypełnia obszary
    """
    if len(points) < min_samples:
        # Za mało punktów - zwykła maska
        mask = np.zeros((grid_size, grid_size), dtype=bool)
        for row, col in points:
            mask[row, col] = True
        return mask
    
    # DBSCAN clustering
    points_array = np.array(points)
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(points_array)
    labels = clustering.labels_
    
    # Utwórz maskę
    mask = np.zeros((grid_size, grid_size), dtype=bool)
    
    # Dla każdego clustera
    unique_labels = set(labels)
    for label in unique_labels:
        if label == -1:  # szum
            continue
        
        # Punkty w tym clusterze
        cluster_points = points_array[labels == label]
        
        # Zaznacz punkty
        for row, col in cluster_points:
            mask[row, col] = True
    
    # MORFOLOGIA: wypełnij dziury, rozszerz lekko, wyczyść
    mask = binary_dilation(mask, iterations=2)  # Rozszerz
    mask = binary_fill_holes(mask)              # Wypełnij dziury
    mask = binary_closing(mask, structure=np.ones((5, 5)))  # Wygładź
    
    return mask

print("🧩 Clusteryzacja i wypełnianie obszarów...\n")

# Utwórz maski dla każdego typu
res_low_mask = create_clustered_mask(res_low_points, grid_size, eps=4, min_samples=10)
res_high_mask = create_clustered_mask(res_high_points, grid_size, eps=3, min_samples=8)
commercial_mask = create_clustered_mask(commercial_points, grid_size, eps=2, min_samples=3)
industrial_mask = create_clustered_mask(industrial_points, grid_size, eps=3, min_samples=5)

print(f"   ✓ Res Low clusters:     {np.sum(res_low_mask)} komórek")
print(f"   ✓ Res High clusters:    {np.sum(res_high_mask)} komórek")
print(f"   ✓ Commercial clusters:  {np.sum(commercial_mask)} komórek")
print(f"   ✓ Industrial clusters:  {np.sum(industrial_mask)} komórek")
print()

# Przypisz do grida (od najniższego priorytetu)
grid[res_low_mask] = 1
grid[res_high_mask] = 2
grid[commercial_mask] = 3
grid[industrial_mask] = 4

# ============================================
# PARKI - wypełnione wielokąty
# ============================================

if parks is not None and len(parks) > 0:
    print("🌲 Parki...")
    
    from matplotlib.path import Path
    
    parks_mask = np.zeros((grid_size, grid_size), dtype=bool)
    
    for idx, feature in parks.iterrows():
        try:
            geom = feature.geometry
            if geom.geom_type != 'Polygon':
                continue
            
            # Konwertuj współrzędne
            coords = []
            for lon, lat in geom.exterior.coords:
                row, col = point_to_grid(lon, lat)
                if row is not None:
                    coords.append([col, row])
            
            if len(coords) < 3:
                continue
            
            # Wypełnij wielokąt
            path = Path(coords)
            exterior = np.array(coords)
            min_col, min_row = exterior.min(axis=0)
            max_col, max_row = exterior.max(axis=0)
            
            min_col = max(0, int(min_col))
            max_col = min(grid_size, int(max_col) + 1)
            min_row = max(0, int(min_row))
            max_row = min(grid_size, int(max_row) + 1)
            
            for row in range(min_row, max_row):
                for col in range(min_col, max_col):
                    if path.contains_point([col, row]):
                        parks_mask[row, col] = True
        except:
            pass
    
    # Wyczyść i rozszerz
    parks_mask = binary_closing(parks_mask, structure=np.ones((3, 3)))
    
    grid[parks_mask] = 5
    print(f"   ✓ {np.sum(parks_mask)} komórek parków\n")

# ============================================
# WODA
# ============================================

if water is not None and len(water) > 0:
    print("💧 Woda...")
    water_count = 0
    
    for idx, feature in water.iterrows():
        try:
            geom = feature.geometry
            if geom.geom_type == 'LineString':
                coords = list(geom.coords)
                for lon, lat in coords:
                    row, col = point_to_grid(lon, lat)
                    if row is not None:
                        for dr in range(-2, 3):
                            for dc in range(-2, 3):
                                r, c = row + dr, col + dc
                                if 0 <= r < grid_size and 0 <= c < grid_size:
                                    grid[r, c] = 6
                                    water_count += 1
        except:
            pass
    
    print(f"   ✓ {water_count} komórek wody\n")

# ============================================
# DROGI - tylko główne
# ============================================

if roads is not None and len(roads) > 0:
    print("🚗 Drogi główne...")
    
    main_types = ['motorway', 'trunk', 'primary', 'secondary']
    road_count = 0
    
    for idx, feature in roads.iterrows():
        try:
            highway = feature.get('highway', '')
            if highway not in main_types:
                continue
            
            geom = feature.geometry
            if geom.geom_type == 'LineString':
                coords = list(geom.coords)
                for lon, lat in coords:
                    row, col = point_to_grid(lon, lat)
                    if row is not None and grid[row, col] not in [6]:
                        grid[row, col] = 7
                        road_count += 1
        except:
            pass
    
    print(f"   ✓ {road_count} komórek dróg\n")

# ============================================
# STATYSTYKI
# ============================================

print("="*50)
print("📊 STATYSTYKI")
print("="*50)

total = grid_size * grid_size
names = ['Empty', 'Res Low', 'Res High', 'Commercial', 'Industrial', 'Parks', 'Water', 'Roads']

for i in range(8):
    count = np.sum(grid == i)
    if count > 0:
        pct = count / total * 100
        bar = '█' * int(pct / 2)
        print(f"{names[i]:15s}: {count:6d} ({pct:5.1f}%) {bar}")


np.save('../krakow_grid.npy', grid)
print(f"✅ Zapisano: krakow_grid.npy")

print("\n🎉 GOTOWE - ciągłe obszary zabudowy!\n")

