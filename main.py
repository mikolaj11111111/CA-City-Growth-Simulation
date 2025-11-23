import streamlit as st
import numpy as np
import time
from visualization import *
from rules_implementations import *

st.set_page_config(layout="wide", page_title="Cellular Automaton - Kraków")

# STREAMLIT APP

st.title("🏙️ Cellular Automaton - Urban Growth Simulation")

# Wczytaj początkowy grid
@st.cache_data
def load_initial_grid():
    try:
        grid = np.load('krakow_grid.npy')
        return grid
    except FileNotFoundError:
        st.error("❌ Nie znaleziono pliku 'krakow_grid.npy'!")
        st.stop()

initial_grid = load_initial_grid()

# Inicjalizacja session state
if 'current_grid' not in st.session_state:
    st.session_state.current_grid = initial_grid.copy()
    st.session_state.iteration = 0

# SIDEBAR - KONTROLKI

st.sidebar.header("⚙️ Kontrola symulacji")

# Wybór trybu
rule_mode = st.sidebar.radio(
    "Tryb reguł",
    ["Pojedyncza reguła", "Wiele reguł"],
    help="Pojedyncza: jedna reguła na raz | Wiele: kombinacja reguł"
)

st.sidebar.markdown("---")

# Definicje reguł
all_rules = {
    "Ekspansja Res Low": "≥N sąsiadów Res Low → Res Low",
    "Gęsta zabudowa": "Empty + ≥N residential → Res High",
    "Gentryfikacja": "Res Low + ≥N Commercial → Commercial",
    "Komercja wzdłuż dróg": "Empty + obok Roads + ≥N residential → Commercial",
    "Suburbanizacja": "Empty + daleko od centrum + ≥2 Res Low → Res Low",
    "Presja na parki": "Parks + ≥N residential → Res Low",
    "Industrializacja peryferii": "Empty + peryferie + blisko Roads → Industrial",
    "Degradacja miejska": "Commercial/Industrial + <2 residential → Empty"
}

# Wybór reguł
if rule_mode == "Pojedyncza reguła":
    selected_rule = st.sidebar.selectbox(
        "Wybierz regułę",
        list(all_rules.keys()),
        help="Pojedyncza reguła do aplikacji"
    )
    st.sidebar.caption(all_rules[selected_rule])
    selected_rules = [selected_rule]
else:
    st.sidebar.markdown("**Wybierz reguły:**")
    selected_rules = []
    for rule_name, description in all_rules.items():
        if st.sidebar.checkbox(rule_name, value=(rule_name == "Ekspansja Res Low"), 
                               help=description):
            selected_rules.append(rule_name)

st.sidebar.markdown("---")

# Parametry reguł
st.sidebar.markdown("**🎛️ Parametry reguł:**")

params = {}

if "Ekspansja Res Low" in selected_rules:
    params['res_low_threshold'] = st.sidebar.slider(
        "Próg Res Low", 1, 8, 3,
        help="Min. sąsiadów Res Low do ekspansji"
    )

if "Gęsta zabudowa" in selected_rules:
    params['high_density_threshold'] = st.sidebar.slider(
        "Próg gęstej zabudowy", 3, 8, 5,
        help="Min. sąsiadów residential dla Res High"
    )

if "Gentryfikacja" in selected_rules:
    params['gentrif_threshold'] = st.sidebar.slider(
        "Próg gentryfikacji", 2, 8, 4,
        help="Min. sąsiadów Commercial"
    )

if "Komercja wzdłuż dróg" in selected_rules:
    params['commercial_threshold'] = st.sidebar.slider(
        "Próg komercji", 1, 5, 2,
        help="Min. sąsiadów residential dla komercji"
    )

if "Suburbanizacja" in selected_rules:
    params['suburban_distance'] = st.sidebar.slider(
        "Dystans suburban", 40, 120, 80,
        help="Min. dystans od centrum"
    )

if "Presja na parki" in selected_rules:
    params['park_threshold'] = st.sidebar.slider(
        "Próg presji na parki", 4, 8, 6,
        help="Min. sąsiadów residential"
    )

st.sidebar.markdown("---")

# Kontrola animacji
iterations = st.sidebar.slider(
    "Liczba iteracji",
    min_value=1,
    max_value=100,
    value=10,
    step=1
)

animation_speed = st.sidebar.slider(
    "Prędkość (sek/krok)",
    min_value=0.05,
    max_value=2.0,
    value=0.3,
    step=0.05
)

col_buttons = st.sidebar.columns(2)
run_button = col_buttons[0].button("▶️ Run", use_container_width=True)
reset_button = col_buttons[1].button("🔄 Reset", use_container_width=True)

if reset_button:
    st.session_state.current_grid = initial_grid.copy()
    st.session_state.iteration = 0
    st.rerun()

# Statystyki
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Iteracja:** {st.session_state.iteration}")

for i, name in enumerate(['Empty', 'Res Low', 'Res High', 'Commercial', 
                          'Industrial', 'Parks', 'Water', 'Roads']):
    count = np.sum(st.session_state.current_grid == i)
    if count > 0:
        pct = (count / st.session_state.current_grid.size) * 100
        st.sidebar.caption(f"{name}: {count} ({pct:.1f}%)")

# LAYOUT GŁÓWNY
# Info o wybranych regułach
if len(selected_rules) > 0:
    with st.expander("📋 Aktywne reguły", expanded=False):
        for rule in selected_rules:
            st.markdown(f"✅ **{rule}**: {all_rules[rule]}")
else:
    st.warning("⚠️ Nie wybrano żadnej reguły!")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🗺️ Początkowy stan")
    initial_img = create_visualization(initial_grid, 0)
    st.image(initial_img, use_container_width=True)

with col2:
    st.subheader(f"🔄 Stan symulacji")
    image_placeholder = st.empty()
    stats_placeholder = st.empty()

# Wyświetl aktualny stan
current_img = create_visualization(st.session_state.current_grid, st.session_state.iteration)
image_placeholder.image(current_img, use_container_width=True)

res_low_count = np.sum(st.session_state.current_grid == 1)
total_cells = st.session_state.current_grid.size
res_low_pct = (res_low_count / total_cells) * 100
stats_placeholder.info(f"**Iteracja {st.session_state.iteration}** | Res Low: {res_low_count} ({res_low_pct:.1f}%)")

# Animacja
if run_button and len(selected_rules) > 0:
    progress_bar = st.sidebar.progress(0)
    
    for i in range(iterations):
        # Aplikuj reguły
        st.session_state.current_grid = apply_rules(
            st.session_state.current_grid, 
            selected_rules, 
            params
        )
        st.session_state.iteration += 1
        
        # Aktualizuj obraz
        current_img = create_visualization(st.session_state.current_grid, st.session_state.iteration)
        image_placeholder.image(current_img, use_container_width=True)
        
        # Statystyki
        res_low_count = np.sum(st.session_state.current_grid == 1)
        res_low_pct = (res_low_count / total_cells) * 100
        stats_placeholder.info(f"**Iteracja {st.session_state.iteration}** | Res Low: {res_low_count} ({res_low_pct:.1f}%)")
        
        # Progress
        progress_bar.progress((i + 1) / iterations)
        
        if i < iterations - 1:
            time.sleep(animation_speed)
    
    progress_bar.empty()
    st.rerun()

# Info
st.markdown("---")
st.info("""
**🎮 Jak używać:**
1. Wybierz tryb: pojedyncza reguła lub wiele reguł naraz
2. Zaznacz reguły które chcesz aktywować
3. Dostosuj parametry (progi, dystanse)
4. Ustaw liczbę iteracji i prędkość animacji
5. Kliknij ▶️ Run aby zobaczyć ewolucję miasta!

**💡 Ciekawe kombinacje:**
- **Realistyczna ekspansja**: Ekspansja Res Low + Suburbanizacja + Komercja wzdłuż dróg
- **Gentryfikacja centrum**: Gentryfikacja + Gęsta zabudowa + Presja na parki
- **Cycles**: Degradacja miejska + Ekspansja Res Low (cykle zabudowy/opuszczenia)
""")