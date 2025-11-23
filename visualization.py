import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import io


def create_visualization(grid, iteration_num=0):
    """Tworzy wizualizację gridu"""
    colors = [
        '#F5F5F5',  # 0: EMPTY
        '#FFF9C4',  # 1: RES LOW
        '#FFB74D',  # 2: RES HIGH
        '#EC407A',  # 3: COMMERCIAL
        '#AB47BC',  # 4: INDUSTRIAL
        '#66BB6A',  # 5: PARKS
        '#42A5F5',  # 6: WATER
        '#616161',  # 7: ROADS
    ]
    
    names = ['Empty', 'Res Low', 'Res High', 'Commercial', 
             'Industrial', 'Parks', 'Water', 'Roads']
    
    cmap = ListedColormap(colors)
    
    fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
    im = ax.imshow(grid, cmap=cmap, vmin=0, vmax=7, interpolation='bilinear')
    
    ax.set_title(f'Iteracja: {iteration_num}', fontsize=16, fontweight='bold')
    ax.set_xlabel('West → East', fontsize=10)
    ax.set_ylabel('North → South', fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])
    
    for spine in ax.spines.values():
        spine.set_edgecolor('#CCCCCC')
        spine.set_linewidth(2)
    
    cbar = plt.colorbar(im, ax=ax, ticks=range(8), fraction=0.046, pad=0.04)
    cbar.set_label('Typ terenu', fontsize=12, fontweight='bold')
    cbar.ax.set_yticklabels(names, fontsize=9)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    
    return buf