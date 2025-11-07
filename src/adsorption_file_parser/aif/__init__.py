"""General parser settings."""

# Mapping of AIF file dictionary keys to meta keys
AIF_VERSION = 'v1.0.0'
META_TO_AIF_MAPPING = {
    '_exptl_operator': 'operator',
    '_exptl_date': 'date',
    '_exptl_adsorptive': 'adsorbate',
    '_exptl_temperature': 'temperature',
    '_exptl_instrument': 'instrument',
    #
    '_adsnt_sample_id': 'material',
    '_adsnt_sample_mass': 'material_mass',
    #
    '_units_temperature': 'temperature_unit',
    '_units_pressure': 'pressure_unit',
    '_units_mass': 'material_unit',
    '_units_loading': 'loading_unit'
}

import os
import numpy as np
import pandas as pd
from gemmi import cif


def aif_data_standardise(meta, data):
    'Change data dict from parser to match an AIF format.'

    # change pressure modes
    p_key = 'pressure'
    if 'pressure' not in data:
        if 'pressure_relative' in data and 'pressure_saturation' in data:
            data['pressure'] = [
                a * b for a, b in zip(data['pressure_relative'], data['pressure_saturation'])
            ]
            meta['pressure_mode'] = 'relative'
            meta['pressure_unit'] = meta['pressure_saturation_unit']
        else:
            p_key = 'pressure_relative'

    # Get to original unparsed strings
    if meta.get('original_pressure_string'):
        meta['pressure_unit'] = meta.pop('original_pressure_string')
    if meta.get('original_loading_string'):
        meta['loading_unit'] = meta.pop('original_loading_string')

    # ensure something is passed
    if meta['pressure_unit'] is None:
        meta['pressure_unit'] = 'relative'

    # remove unneeded keys
    meta.pop("pressure_mode")
    meta.pop("loading_basis")
    meta.pop("material_basis")

    # split ads / desorption branches
    if 'branch' in data:
        if 1 in data['branch']:
            turnp = data['branch'].index(1)
        else:
            turnp = len(data['branch'])
        del data['branch']
    else:
        turnp = np.argmax(data[p_key]) + 1

    data_ads = {}
    data_des = {}

    for key, val in data.items():
        data_ads[key] = val[:turnp]
        data_des[key] = val[turnp:]

    data_ads = pd.DataFrame(data_ads)
    data_des = pd.DataFrame(data_des)

    return meta, data_ads, data_des


# write adsorption file
def make_aif(filename, meta, data):
    """Compose AIF dictionary and output to file"""

    meta, data_ads, data_des = aif_data_standardise(meta, data)

    # initialize aif block
    aif = cif.Document()
    aif.add_new_block('afp_aif')
    block = aif.sole_block()

    # write version
    block.set_pair('_audit_aif_version', AIF_VERSION)

    # write known metadata
    for key, value in META_TO_AIF_MAPPING.items():
        if not meta[value] or meta[value] == '':
            meta.pop(value)
            block.set_pair(key, r'"unknown"')
        else:
            block.set_pair(key, f'"{(meta.pop(value))}"')

    # write all other metadata
    filetype = meta.pop('filetype', 'afp')
    for key, value in meta.items():
        block.set_pair(f'_{filetype}_{key}', f'"{value}"')

    #check if saturation pressure is for every point
    # warning: what if none of these conditions are correct
    # i.e. saturation_pressure is not given at all?
    if 'pressure_saturation' in data_ads:
        # write adsorption data
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'p0', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['pressure_saturation'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            loop_des = block.init_loop('_desorp_', ['pressure', 'p0', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['pressure_saturation'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    # warning: this branch can never be reached
    elif 'pressure_saturation' in data_ads and len(list(meta['pressure_saturation'])) == 1:
        block.set_pair('_exptl_p0', str(meta['pressure_saturation'][0]))
        # write adsorption data
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            loop_des = block.init_loop('_desorp_', ['pressure', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    elif 'pressure_saturation' not in data_ads and 'pressure_relative' in data_ads:
        # write adsorption data
        data_ads['pressure_saturation'] = (1 / data_ads['pressure_relative']) * data_ads['pressure']
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'p0', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['pressure_saturation'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            data_des['pressure_saturation'] = (1 /
                                               data_des['pressure_relative']) * data_des['pressure']
            loop_des = block.init_loop('_desorp_', ['pressure', 'p0', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['pressure_saturation'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    else:
        # write adsorption data
        loop_ads = block.init_loop('_adsorp_', ['pressure', 'amount'])
        loop_ads.set_all_values([
            list(data_ads['pressure'].astype(str)),
            list(data_ads['loading'].astype(str))
        ])

        # write desorption data
        if len(data_des > 0):
            loop_des = block.init_loop('_desorp_', ['pressure', 'amount'])
            loop_des.set_all_values([
                list(data_des['pressure'].astype(str)),
                list(data_des['loading'].astype(str))
            ])

    outputfilename = os.path.splitext(filename)[0] + '.aif'
    aif.write_file(outputfilename)
