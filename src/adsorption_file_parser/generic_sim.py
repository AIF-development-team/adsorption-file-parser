import os
import numpy as np
from datetime import datetime
from gemmi import cif

def parse_file(path, input_data):
    """
    Parses a 3-column whitespace file from custom simulations.
    
    Col 1: P/P0
    Col 2: loading (molecules/asym unit)
    Col 3: uncertainty (molecules/asym unit)

    Args:
        path (str): Path to the input file.
        input_data (dict): Dictionary containing conversion factors and metadata:
            Physical Parameters:
              - 'm_cell_amu': mass of unit cell (g/mol)
              - 'asym_to_cell': molecules per cell / molecules per asymmetric unit
              - 'saturation_pressure': P0 (bar)
            Metadata:
              - 'operator': Name of the simulation operator
              - 'adsorbate': Name of the adsorbate (e.g., 'water')
              - 'temperature': Simulation temperature
              - 'temperature_unit': Unit for temperature (e.g., 'K')
              - 'pressure_unit': Unit for pressure (e.g., 'bar')
              - 'material_id': Name/ID of the material
              - 'simulation_lot': Simulation batch/lot identifier
              - 'citation': DOI or reference for the simulation
              - 'input_files': Path or description of input files used
              - 'sampling_method': Monte Carlo sampling method (e.g., 'GCMC')
    
    Returns:
        (meta, data): Parser result tuple.
    """
    
    # Validate required keys
    required_keys = [
        'm_cell_amu', 'asym_to_cell', 'saturation_pressure',
        'operator', 'adsorbate', 'temperature', 'temperature_unit',
        'pressure_unit', 'material_id', 'simulation_lot',
        'citation', 'input_files', 'sampling_method'
    ]
    
    missing = [key for key in required_keys if key not in input_data]
    if missing:
        raise ValueError(f"Custom parser missing required keys in input_data: {', '.join(missing)}")

    # Setup conversion factors
    # Formula: (mols/cell) * (1000 g/kg) / (g/mol cell mass)
    conv_factor = input_data['asym_to_cell'] * 1000.0 / input_data['m_cell_amu']
    p0 = input_data['saturation_pressure']

    # Load data from file
    try:
        arr = np.loadtxt(path)
    except Exception as e:
        raise ValueError(f"Could not read custom file {path}: {e}")

    # Handle single data point (1D array) vs multiple (2D array)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)

    rel_p = arr[:, 0]
    uptake_asym = arr[:, 1]
    uncertainty_asym = arr[:, 2]

    # Perform unit conversions
    uptake_molkg = uptake_asym * conv_factor
    uncertainty_molkg = uncertainty_asym * conv_factor

    # Populate metadata from input_data
    meta = {
        'operator': input_data['operator'],
        'date': datetime.now().date().isoformat(),
        'apparatus': 'simulation',
        'experimental_method': 'simulation',
        'adsorbate': input_data['adsorbate'],
        'temperature': input_data['temperature'],
        'temperature_unit': input_data['temperature_unit'],
        'pressure_unit': input_data['pressure_unit'],
        'loading_unit': 'mol/kg',
        'pressure_mode': 'absolute',
        'material_id': input_data['material_id'],
        'simulation_lot': input_data['simulation_lot'],
        'simulation_code': 'custom',
        'citation': input_data['citation'],
        'input_files': input_data['input_files'],
        'sampling_method': input_data['sampling_method'],
        'saturation_pressure': input_data['saturation_pressure']
    }

    # Structure data points
    data = {
        'pressure_relative': list(rel_p),
        'pressure':          list(rel_p * p0),
        'loading':           list(uptake_molkg),
        'uncertainty':       list(uncertainty_molkg)
    }

    return meta, data


def makeAIF(data_meta, data_ads, filename):
    """
    Creates an AIF (Adsorption Information File) from parsed simulation data.
    
    Args:
        data_meta (dict): Metadata dictionary from parse_file.
        data_ads (dict): Adsorption data dictionary from parse_file.
        filename (str): Output filename (extension will be replaced with .aif).
    """
    doc = cif.Document()
    doc.add_new_block('custom2aif')
    block = doc.sole_block()

    block.set_pair('_audit_aif_version', 'a0d6475')

    # Experimental metadata
    block.set_pair('_exptl_operator',        str(data_meta['operator']))
    block.set_pair('_exptl_method',          str(data_meta['experimental_method']))
    block.set_pair('_exptl_isotherm_type',   str(data_meta['pressure_mode']))
    block.set_pair('_exptl_adsorptive',      str(data_meta['adsorbate']))
    block.set_pair('_exptl_temperature',     str(data_meta['temperature']))
    block.set_pair('_exptl_p0',              str(data_meta['saturation_pressure']))

    # Adsorbent material
    block.set_pair('_adsnt_material_id',     str(data_meta['material_id']))

    # Simulation metadata
    block.set_pair('_simltn_date',           data_meta['date'])
    block.set_pair('_simltn_code',           str(data_meta['simulation_code']))
    block.set_pair('_simltn_sampling',       str(data_meta['sampling_method']))
    block.set_pair('_simltn_input_files',    str(data_meta['input_files']))
    block.set_pair('_simltn_lot',            str(data_meta['simulation_lot']))

    # Units
    block.set_pair('_units_temperature',     str(data_meta['temperature_unit']))
    block.set_pair('_units_loading',         str(data_meta['loading_unit']))
    block.set_pair('_units_pressure',        str(data_meta['pressure_unit']))

    # Citation
    block.set_pair('_citation_doi',          str(data_meta['citation']))

    # Adsorption data loop with uncertainty
    loop = block.init_loop('_adsorp_',
                           ['pressure', 'amount', 'amount_uncertainty'])
    loop.set_all_values([
        list(map(str, data_ads['pressure'])),
        list(map(str, data_ads['loading'])),
        list(map(str, data_ads['uncertainty']))
    ])

    outname = os.path.splitext(filename)[0] + '.aif'
    doc.write_file(outname)