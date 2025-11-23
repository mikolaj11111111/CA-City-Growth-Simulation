from ca_rules import *

def apply_rules(grid, selected_rules, params):
    """Aplikuje wybrane reguły do gridu"""
    new_grid = grid.copy()
    
    for rule_name in selected_rules:
        if rule_name == "Ekspansja Res Low":
            new_grid = rule_res_low_expansion(new_grid, params['res_low_threshold'])
        elif rule_name == "Gęsta zabudowa":
            new_grid = rule_high_density(new_grid, params['high_density_threshold'])
        elif rule_name == "Gentryfikacja":
            new_grid = rule_gentrification(new_grid, params['gentrif_threshold'])
        elif rule_name == "Komercja wzdłuż dróg":
            new_grid = rule_commercial_roads(new_grid, params['commercial_threshold'])
        elif rule_name == "Suburbanizacja":
            new_grid = rule_suburban_sprawl(new_grid, params['suburban_distance'])
        elif rule_name == "Presja na parki":
            new_grid = rule_park_pressure(new_grid, params['park_threshold'])
        elif rule_name == "Industrializacja peryferii":
            new_grid = rule_industrial_periphery(new_grid)
        elif rule_name == "Degradacja miejska":
            new_grid = rule_urban_decay(new_grid)
    
    return new_grid
