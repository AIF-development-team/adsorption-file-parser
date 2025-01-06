from gemmi import cif
import numpy as np
import pandas as pd

def quoted(text):
    """Add a single quote around an argument."""
    return "'" + text + "'"

def aif_data_standardise(meta, data):
    'Change data dict from parser to match  an AIF format.'

    # change pressure modes
    p_key = 'pressure'
    if 'pressure' not in data:
        if 'pressure_relative' in data and 'pressure_saturation' in data:
            data['pressure'] = [
                a * b for a, b in zip(data['pressure_relative'],
                                      data['pressure_saturation'])
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
    if 'pressure_unit' in meta:
        if meta['pressure_unit'] is None:
            meta['pressure_unit'] = 'relative'

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


def makeAIF(data_meta, data_ads, data_des):
    """Compose AIF dictionary and output to file"""
    # initialize aif block
    d = cif.Document()

    d.add_new_block('raw2aif')

    block = d.sole_block()

    # write metadata
    if not data_meta['operator'] or data_meta['operator'] == '':
        block.set_pair('_exptl_operator', quoted('unknown'))
    else:
        block.set_pair('_exptl_operator', quoted(data_meta['operator']))
    block.set_pair('_exptl_date', data_meta['date'])
    if 'apparatus' not in data_meta:
        block.set_pair('_exptl_instrument', 'unknown')
    else:
        block.set_pair('_exptl_instrument', quoted(data_meta['apparatus']))
    block.set_pair('_exptl_adsorptive', quoted(data_meta['adsorbate']))
    block.set_pair('_exptl_temperature', str(data_meta['temperature']))
    block.set_pair('_adsnt_sample_mass', str(data_meta['material_mass']))

    block.set_pair('_adsnt_sample_id', quoted(data_meta['material']))

    block.set_pair('_units_temperature', quoted(data_meta['temperature_unit']))
    block.set_pair('_units_pressure', quoted(data_meta['pressure_unit']))
    block.set_pair('_units_mass', quoted(data_meta['material_unit']))
    block.set_pair('_units_loading', quoted(data_meta['loading_unit']))
    block.set_pair('_audit_aif_version', '0.01')

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
    elif 'pressure_saturation' in data_ads and len(list(data_meta['pressure_saturation'])) == 1:
        block.set_pair('_exptl_p0', str(data_meta['pressure_saturation'][0]))
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

    return d


# write adsorption file
def makeAIF_generic(data_meta, data_ads, data_des):
    """Compose AIF dictionary and output to file"""
    # initialize aif block
    d = cif.Document()

    d.add_new_block('raw2aif')

    block = d.sole_block()

    # write metadata
    for key in data_meta:
        if type(data_meta[key]) == str:
            block.set_pair(key, quoted(data_meta[key]))
        else:
            block.set_pair(key, str(data_meta[key]))

    block.set_pair('_audit_aif_version', '0.01')

    #check if saturation pressure is for every point
    # warning: what if none of these conditions are correct
    # i.e. saturation_pressure is not given at all?
   
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

    return d