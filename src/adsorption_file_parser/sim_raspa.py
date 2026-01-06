#!/usr/bin/env python3
"""
Convert RASPA adsorption outputs into Adsorption Information Files (AIF).

This script parses RASPA *.data files (typically under System_0/) and writes AIF
representations for:
  - single-component GCMC isotherms
  - multicomponent GCMC isotherms (including selectivity)
  - Widom insertion results (Henry coefficient + adsorption enthalpy)

Usage:
    python raspa2aif.py <raspa_output_dir> [output.aif]

Args:
    raspa_output_dir: Path to a RASPA run directory containing System_0/
                      with one or more *.data files.
    output.aif: Optional output AIF filename (used for single- and
                multicomponent modes). If omitted, uses default naming.

Notes:
    Mode detection is automatic:
      - Widom insertion mode is triggered when Widom-style result files are
        detected (distinguished by filename patterns/content and force-field labels).
      - Multicomponent mode is used when multiple adsorbate components are found.
      - Otherwise, the script assumes single-component GCMC.
    In Widom mode, the script writes one AIF per force-field combination,
    so output.aif may be ignored and naming is handled internally.

Expected input layout:
    <raspa_output_dir>/
      System_0/
        *.data
"""

import os
import sys
import glob
import re
from datetime import datetime

import numpy as np
import pandas as pd
from gemmi import cif


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_float_re = re.compile(r"[-+]?\d*\.\d+(?:[Ee][+-]?\d+)?|[-+]?\d+(?:[Ee][+-]?\d+)?")
_mf_re = re.compile(
    r"MolFraction:?[ \t]+"
    r"([-+]?\d*\.?\d+(?:[Ee][+-]?\d+)?)"
    r"(?:[ \t]*\[.*?\])?",
    re.IGNORECASE,
)
_md_re = re.compile(r"MoleculeDefinitions?:?[ \t]+(\S+)", re.IGNORECASE)


def checkifunique(df, col):
    """Warn (but do not abort) if a metadata column is not unique."""
    if col not in df.columns:
        return
    if df[col].nunique() != 1:
        print(f"Warning: {col} not unique in dataframe")


def detect_mode(input_dir):
    """
    Detect which kind of RASPA output we are dealing with.

    Args:
        input_dir (str): Path to the RASPA output directory.

    Returns:
        str: One of 'widom', 'multicomponent', or 'single'.
    """
    paths = glob.glob(os.path.join(input_dir, "System_0", "*.data"))
    if not paths:
        sys.exit(f"Error: no .data files found under '{input_dir}'")

    # Widom detection based on filename pattern:
    # Widom jobs use a forcefield name as the LAST token in the filename
    # (e.g. ..._303.000000_AMBER.data), which is NON-numeric.
    # Isotherm jobs use a numeric pressure as the last token
    # (e.g. ..._300.000000_1000.data).
    numeric_last = False
    non_numeric_last = False
    for fn in paths:
        base = os.path.splitext(os.path.basename(fn))[0]
        last = base.split("_")[-1]
        try:
            float(last)
        except ValueError:
            non_numeric_last = True
        else:
            numeric_last = True

    # If all last tokens are non-numeric, treat directory as Widom mode
    if non_numeric_last and not numeric_last:
        return "widom"

    # Multicomponent detection:
    # Multicomponent simulations have multiple "(Adsorbate molecule)"
    # lines in the header (one per component). Single-component and
    # Widom runs only have one.
    for fn in paths:
        ads_count = 0
        with open(fn) as f:
            for line in f:
                if "(Adsorbate molecule)" in line or "(adsorbate molecule)" in line.lower():
                    ads_count += 1
        if ads_count > 1:
            return "multicomponent"

    # Fallback: single-component GCMC
    return "single"


# ---------------------------------------------------------------------------
# Single-Component GCMC
# ---------------------------------------------------------------------------

def parse_single_component(input_dir):
    """
    Parse single-component GCMC output files from RASPA.

    Args:
        input_dir (str): Path to the RASPA output directory.

    Returns:
        pd.DataFrame: Parsed isotherm data sorted by pressure.
    """
    outputs = glob.glob(os.path.join(input_dir, "System_0", "*.data"))
    if not outputs:
        sys.exit(f"Error: no .data files found under '{input_dir}'")

    data = []
    for output in outputs:
        with open(output) as f:
            output_split = os.path.splitext(os.path.basename(output))[0].split('_')
            temperature = output_split[-2]
            pressure = output_split[-1]
            code = ""
            time = ""
            operator = ""
            framework_name = ""
            adsorbate_name = ""
            adsorbate_definition = ""
            ff_definition = ""
            loading = ""
            loading_error = ""
            excess_loading = ""
            excess_loading_error = ""
            enthalpy = ""
            enthalpy_error = ""

            for index, line in enumerate(f):
                if index == 2:
                    code = line.strip('\n').replace(' ', '-')
                elif index == 7:
                    time = datetime.strptime(line.strip('\n'), "%a %b %d %H:%M:%S %Y")
                elif "Hostname:" in line:
                    operator = line.split()[-1]
                elif "Framework name:" in line:
                    framework_name = line.split()[-1]
                elif "Forcefield: " in line:
                    ff_definition = line.split()[-1]
                elif "(Adsorbate molecule)" in line:
                    adsorbate_name = line.split()[2].strip("[]")
                elif "MoleculeDefinitions: " in line:
                    adsorbate_definition = line.split()[-1]
                elif "Average loading absolute [mol/kg framework]" in line:
                    loading = float(line.split()[5])
                    loading_error = float(line.split()[7])
                elif "Average loading excess [mol/kg framework]" in line:
                    excess_loading = float(line.split()[5])
                    excess_loading_error = float(line.split()[7])
                elif "[KJ/MOL]" in line:
                    enthalpy = float(line.split()[0])
                    enthalpy_error = float(line.split()[2])

            data.append({
                "temperature": temperature,
                "pressure": pressure,
                "code": code,
                "time": time,
                "operator": operator,
                "framework_name": framework_name,
                "adsorbate_name": adsorbate_name,
                "adsorbate_definition": adsorbate_definition,
                "ff_definition": ff_definition,
                "loading": loading,
                "loading_error": loading_error,
                "excess_loading": excess_loading,
                "excess_loading_error": excess_loading_error,
                "enthalpy": enthalpy,
                "enthalpy_error": enthalpy_error,
            })

    df = pd.DataFrame(data)
    df = df.sort_values(by=["pressure"])
    return df


def write_single_component_aif(df, output_file=None):
    """
    Write a single-component GCMC isotherm to an AIF file.

    Args:
        df (pd.DataFrame): Parsed isotherm data from parse_single_component.
        output_file (str, optional): Output filename. Defaults to
                                     <framework>_<adsorbate>_<T>K.aif.
    """
    if output_file is None:
        ads = str(df["adsorbate_name"].iloc[0])
        fw = str(df["framework_name"].iloc[0])
        T = str(df["temperature"].iloc[0])
        output_file = f"{fw}_{ads}_{T}K.aif"

    d = cif.Document()
    d.add_new_block("raspa2aif")
    block = d.sole_block()
    block.set_pair("_audit_aif_version", "a0d6475")

    # Experimental metadata
    checkifunique(df, "operator")
    block.set_pair("_exptl_operator", str(df["operator"].iloc[0]))
    block.set_pair("_exptl_method", "simulation")
    block.set_pair("_exptl_isotherm_type", "absolute")
    checkifunique(df, "adsorbate_name")
    block.set_pair("_exptl_adsorptive", str(df["adsorbate_name"].iloc[0]))
    checkifunique(df, "temperature")
    block.set_pair("_exptl_temperature", str(df["temperature"].iloc[0]))

    # Adsorbent material
    checkifunique(df, "framework_name")
    block.set_pair("_adsnt_material_id", str(df["framework_name"].iloc[0]))

    # Simulation metadata
    block.set_pair("_simltn_date", str(pd.to_datetime(df["time"]).mean().isoformat()))
    checkifunique(df, "code")
    block.set_pair("_simltn_code", str(df["code"].iloc[0]))
    block.set_pair("_simltn_sampling", "GCMC")
    block.set_pair(
        "_simltn_input_files",
        f"simulation.input,{df['framework_name'].iloc[0]}.cif",
    )
    checkifunique(df, "adsorbate_definition")
    block.set_pair(
        "_simltn_forcefield_adsorptive",
        str(df["adsorbate_definition"].iloc[0]),
    )
    checkifunique(df, "ff_definition")
    block.set_pair("_simltn_forcefield_adsorbent", str(df["ff_definition"].iloc[0]))

    # Units
    block.set_pair("_units_temperature", "K")
    block.set_pair("_units_energy", "kJ/mol")
    block.set_pair("_units_loading", "mol/kg")
    block.set_pair("_units_pressure", "Pa")

    # Adsorption data loop
    loop_ads = block.init_loop(
        "_adsorp_",
        [
            "pressure",
            "amount",
            "amount_uncertainty",
            "amount_excess",
            "amount_excess_uncertainty",
            "enthalpy",
            "enthalpy_uncertainty",
        ],
    )
    loop_ads.set_all_values(
        [
            ["%.5E" % val for val in df["pressure"].astype(float)],
            ["%.5E" % val for val in df["loading"].astype(float)],
            ["%.5E" % val for val in df["loading_error"].astype(float)],
            ["%.5E" % val for val in df["excess_loading"].astype(float)],
            ["%.5E" % val for val in df["excess_loading_error"].astype(float)],
            ["%.5E" % val for val in df["enthalpy"].astype(float)],
            ["%.5E" % val for val in df["enthalpy_error"].astype(float)],
        ]
    )

    d.write_file(output_file)
    print(f"[single] Wrote AIF to {output_file}")


# ---------------------------------------------------------------------------
# Multicomponent GCMC
# ---------------------------------------------------------------------------

def parse_multicomponent(input_dir):
    """
    Parse multicomponent GCMC output files from RASPA.

    Args:
        input_dir (str): Path to the RASPA output directory.

    Returns:
        tuple: (df_long, comp_names, fractions, definitions) where:
            - df_long: DataFrame with loading data in long format
            - comp_names: List of component names
            - fractions: List of mole fractions
            - definitions: List of molecule definitions
    """
    paths = sorted(glob.glob(os.path.join(input_dir, "System_0", "*.data")))
    if not paths:
        sys.exit(f"Error: no .data files found under '{input_dir}'")

    records = []
    comp_names = []
    fractions = []
    definitions = []

    for fn in paths:
        base = os.path.basename(fn)
        parts = os.path.splitext(base)[0].split("_")
        try:
            T = float(parts[-2])
            P = float(parts[-1])
        except Exception:
            raise ValueError(f"File '{base}' must end in '_<T>_<P>.data'")

        code = ""
        operator = ""
        framework = ""
        ff = ""
        time_stamp = None
        loads = []
        errs = []
        local_names = []
        local_fracs = []
        local_defs = []

        with open(fn) as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            l = line.strip()
            low = l.lower()

            if "(adsorbate molecule)" in low:
                m = re.search(r"\[(.*?)\]", l)
                if not m:
                    raise ValueError(f"Cannot parse component name in line: {l}")
                local_names.append(m.group(1))
                continue

            if "molfraction" in low and local_names:
                mm = _mf_re.search(l)
                if not mm:
                    raise ValueError(f"Cannot parse MolFraction in line: {l}")
                local_fracs.append(float(mm.group(1)))
                continue

            md = _md_re.search(l)
            if md and local_names:
                local_defs.append(md.group(1))
                continue

            if idx == 2 and l:
                code = l.replace(" ", "-")
            elif idx == 7 and not time_stamp:
                try:
                    time_stamp = datetime.strptime(l, "%a %b %d %H:%M:%S %Y")
                except ValueError:
                    pass
            elif low.startswith("hostname:"):
                operator = l.split()[-1]
            elif low.startswith("framework name:"):
                framework = l.split()[-1]
            elif low.startswith("forcefield:") and "adsorbate" not in low:
                ff = l.split()[-1]

            if "average loading absolute" in low and "[mol/kg framework]" in low:
                nums = _float_re.findall(l)
                if len(nums) >= 2:
                    loads.append(float(nums[0]))
                    errs.append(float(nums[1]))

        # Validate parsed data
        if len(local_names) < 2 or len(local_fracs) < 2 or len(local_defs) < 2:
            raise ValueError(
                f"File '{base}': parsed {len(local_names)} names, "
                f"{len(local_fracs)} fractions, {len(local_defs)} definitions"
            )
        if len(loads) < 2:
            raise ValueError(
                f"File '{base}': found only {len(loads)} loading lines, need at least 2"
            )

        if not comp_names:
            comp_names = local_names[:2]
            fractions = local_fracs[:2]
            definitions = local_defs[:2]

        loads = loads[:2]
        errs = errs[:2]
        for j in range(2):
            records.append(
                {
                    "temperature": T,
                    "pressure": P,
                    "code": code,
                    "time": time_stamp,
                    "operator": operator,
                    "framework": framework,
                    "ff": ff,
                    "adsorbate": local_names[j],
                    "loading": loads[j],
                    "loading_err": errs[j],
                }
            )

    return pd.DataFrame(records), comp_names, fractions, definitions


def write_multicomponent_aif(df_long, comp_names, fractions, definitions, output_file=None):
    """
    Write a multicomponent GCMC isotherm to an AIF file.

    Args:
        df_long (pd.DataFrame): Parsed data from parse_multicomponent.
        comp_names (list): Component names [comp0, comp1].
        fractions (list): Mole fractions [y0, y1].
        definitions (list): Molecule definitions [def0, def1].
        output_file (str, optional): Output filename. Defaults to
                                     <framework>_<ads1>-<ads2>_<T>K.aif.
    """
    comp0, comp1 = comp_names

    if output_file is None:
        framework = str(df_long["framework"].iloc[0])
        T = str(df_long["temperature"].iloc[0])
        output_file = f"{framework}_{comp0}-{comp1}_{T}K.aif"

    y0, y1 = fractions
    def0, def1 = definitions

    # Pivot to wide format
    pivot = df_long.pivot_table(
        index=["temperature", "pressure", "operator", "framework", "ff", "time", "code"],
        columns="adsorbate",
        values=["loading", "loading_err"],
    )
    df_wide = pivot.reset_index()
    df_wide.columns = [
        f"{a}_{b}" if b else a for a, b in df_wide.columns.to_flat_index()
    ]

    # Calculate selectivities
    qi = df_wide[f"loading_{comp0}"]
    qj = df_wide[f"loading_{comp1}"]
    sel12 = (qi / qj) / (y0 / y1)
    sel21 = (qj / qi) / (y1 / y0)

    doc = cif.Document()
    doc.add_new_block("multicomponent_raspa2aif")
    blk = doc.sole_block()

    blk.set_pair("_audit_aif_version", "a0d6475s")

    # Experimental metadata
    blk.set_pair("_exptl_operator", str(df_wide["operator"].iloc[0]))
    blk.set_pair("_exptl_method", "simulation")
    blk.set_pair("_exptl_isotherm_type", "absolute")
    blk.set_pair("_exptl_adsorptive1", comp0)
    blk.set_pair("_exptl_adsorptive2", comp1)
    blk.set_pair("_exptl_temperature", str(df_wide["temperature"].iloc[0]))

    # Adsorbent material
    blk.set_pair("_adsnt_material_id", str(df_wide["framework"].iloc[0]))

    # Simulation metadata
    blk.set_pair(
        "_simltn_date",
        str(pd.to_datetime(df_wide["time"]).mean().isoformat()),
    )
    blk.set_pair("_simltn_code", str(df_wide["code"].iloc[0]))
    blk.set_pair("_simltn_sampling", "GCMC")
    blk.set_pair(
        "_simltn_input_files",
        f"simulation.input,{df_wide['framework'].iloc[0]}.cif",
    )
    blk.set_pair("_simltn_forcefield_adsorbent", str(df_wide["ff"].iloc[0]))
    blk.set_pair("_simltn_forcefield_adsorptive1", def0)
    blk.set_pair("_simltn_forcefield_adsorptive2", def1)

    # Units
    blk.set_pair("_units_temperature", "K")
    blk.set_pair("_units_energy", "kJ/mol")
    blk.set_pair("_units_loading", "mol/kg")
    blk.set_pair("_units_pressure", "Pa")

    # Adsorption data loop
    n = len(df_wide)
    mf1 = [f"{y0:.5E}" for _ in range(n)]
    mf2 = [f"{y1:.5E}" for _ in range(n)]
    amt1 = [f"{v:.5E}" for v in df_wide[f"loading_{comp0}"]]
    unc1 = [f"{v:.5E}" for v in df_wide[f"loading_err_{comp0}"]]
    amt2 = [f"{v:.5E}" for v in df_wide[f"loading_{comp1}"]]
    unc2 = [f"{v:.5E}" for v in df_wide[f"loading_err_{comp1}"]]
    s12_vals = [f"{v:.5E}" for v in sel12]
    s21_vals = [f"{v:.5E}" for v in sel21]

    cols = [
        "pressure",
        "molefraction1",
        "molefraction2",
        "amount_absolute1",
        "amount_absolute1_uncertainty",
        "amount_absolute2",
        "amount_absolute2_uncertainty",
        "selectivity12",
        "selectivity21",
    ]
    data = [
        [f"{p:.5E}" for p in df_wide["pressure"]],
        mf1,
        mf2,
        amt1,
        unc1,
        amt2,
        unc2,
        s12_vals,
        s21_vals,
    ]
    loop = blk.init_loop("_adsorp_", cols)
    loop.set_all_values(data)

    doc.write_file(output_file)
    print(f"[multicomponent] Wrote AIF to {output_file}")


# ---------------------------------------------------------------------------
# Widom Insertion (Henry coefficients)
# ---------------------------------------------------------------------------

def parse_widom(input_dir):
    """
    Parse Widom insertion output files from RASPA.

    Args:
        input_dir (str): Path to the RASPA output directory.

    Returns:
        pd.DataFrame: Parsed Henry coefficient data sorted by host force field.
    """
    outputs = glob.glob(os.path.join(input_dir, "System_0", "*.data"))
    if not outputs:
        sys.exit(f"Error: no .data files found under '{input_dir}'")

    data = []
    for output in outputs:
        with open(output) as f:
            print("Output:", output)
            parts = os.path.splitext(os.path.basename(output))[0].split('_')
            temperature = parts[-2]
            host_ff_definition = parts[-1]

            code = ""
            time = None
            operator = ""
            framework_name = ""
            adsorbate_name = ""
            guest_ff_definition = ""
            henry = None
            henry_error = None
            pre_enthalpy = None
            enthalpy = None
            enthalpy_error = None

            for idx, line in enumerate(f):
                if idx == 2:
                    code = line.strip().replace(' ', '-')
                elif idx == 7:
                    time = datetime.strptime(line.strip(), "%a %b %d %H:%M:%S %Y")
                elif "Hostname:" in line:
                    operator = line.split()[-1]
                elif "Framework name:" in line:
                    framework_name = line.split()[-1]
                elif "(Adsorbate molecule)" in line:
                    adsorbate_name = line.split()[2].strip("[]")
                elif "MoleculeDefinitions:" in line:
                    guest_ff_definition = line.split()[-1]
                elif "] Average Henry coefficient:" in line:
                    parts_line = line.split()
                    henry = float(parts_line[4])
                    henry_error = float(parts_line[6])
                elif "<U_gh>_1-<U_h>_0:" in line:
                    parts_line = line.split()
                    pre_enthalpy = float(parts_line[8])
                    enthalpy_error = float(parts_line[10])

            # Validate: if these are missing, this is not a valid WI file
            if pre_enthalpy is None or henry is None:
                raise ValueError(
                    f"File '{output}' does not contain Widom enthalpy/Henry data "
                    "expected for WI mode."
                )

            # Calculate enthalpy with RT correction
            enthalpy = pre_enthalpy - (8.31446261815324 / 1000.0) * float(temperature)

            data.append({
                "temperature": temperature,
                "code": code,
                "time": time,
                "operator": operator,
                "framework_name": framework_name,
                "adsorbate_name": adsorbate_name,
                "host_ff_definition": host_ff_definition,
                "guest_ff_definition": guest_ff_definition,
                "henry": henry,
                "henry_error": henry_error,
                "enthalpy": enthalpy,
                "enthalpy_error": enthalpy_error,
            })

    df = pd.DataFrame(data)
    df = df.sort_values(by=["host_ff_definition"])
    return df


def write_widom_aif(df, output_file=None):
    """
    Write Widom insertion results to AIF files (one per force-field combination).

    Args:
        df (pd.DataFrame): Parsed Widom data from parse_widom.
    """
    checkifunique(df, "operator")
    checkifunique(df, "adsorbate_name")
    checkifunique(df, "framework_name")
    checkifunique(df, "temperature")
    checkifunique(df, "code")

    for idx, row in df.iterrows():
        doc = cif.Document()
        doc.add_new_block("WI_raspa2aif")
        block = doc.sole_block()
        block.set_pair("_audit_aif_version", "a0d6475")

        # Experimental metadata
        block.set_pair("_exptl_operator", str(row.operator))
        block.set_pair("_exptl_method", "simulation")
        block.set_pair("_exptl_adsorptive", str(row.adsorbate_name))
        block.set_pair("_exptl_temperature", str(row.temperature))

        # Adsorbent material
        block.set_pair("_adsnt_material_id", str(row.framework_name))

        # Simulation metadata
        block.set_pair("_simltn_date", row.time.isoformat())
        block.set_pair("_simltn_code", str(row.code))
        block.set_pair("_simltn_sampling", "WI")
        block.set_pair(
            "_simltn_input_files",
            f"simulation.input,{row.framework_name}.cif",
        )
        block.set_pair(
            "_simltn_forcefield_adsorbent",
            str(row.host_ff_definition),
        )
        block.set_pair(
            "_simltn_forcefield_adsorptive",
            str(row.guest_ff_definition),
        )

        # Units
        block.set_pair("_units_temperature", "K")
        block.set_pair("_units_pressure", "Pa")
        block.set_pair("_units_henry", "mol/kg/Pa")
        block.set_pair("_units_enthalpy", "kJ/mol")

        # Adsorption data loop
        loop_ads = block.init_loop(
            "_adsorp_",
            [
                "henry",
                "henry_uncertainty",
                "enthalpy",
                "enthalpy_uncertainty",
            ],
        )
        loop_ads.set_all_values(
            [
                [f"{float(row.henry):.5E}"],
                [f"{float(row.henry_error):.5E}"],
                [f"{float(row.enthalpy):.5E}"],
                [f"{float(row.enthalpy_error):.5E}"],
            ]
        )

        # Output filename: <framework>_<adsorbate>_<T>K.aif
        fw = str(row.framework_name)
        ads = str(row.adsorbate_name)
        T = str(row.temperature)
        if output_file is None:
            out_name = f"{fw}_{ads}_{T}K.aif"
        else:
            out_name = output_file

        doc.write_file(out_name)
        print(f"[widom] Wrote AIF file: {out_name}")


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def main():
    """Main entry point for the raspa2aif converter."""
    if len(sys.argv) < 2:
        sys.exit(f"Usage: {sys.argv[0]} PATH_TO_OUTPUT [OUTPUT_AIF]")

    input_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None

    mode = detect_mode(input_dir)
    print(f"Detected RASPA output mode: {mode}")

    if mode == "single":
        df = parse_single_component(input_dir)
        write_single_component_aif(df, output_file)
    elif mode == "multicomponent":
        df_long, comp_names, fractions, definitions = parse_multicomponent(input_dir)
        write_multicomponent_aif(df_long, comp_names, fractions, definitions, output_file)
    elif mode == "widom":
        df = parse_widom(input_dir)
        if output_file is not None:
            print(
                "Warning: OUTPUT_AIF is ignored in Widom mode "
                "(one file per FF combination).",
                file=sys.stderr,
            )
        write_widom_aif(df)
    else:
        sys.exit(f"Unknown mode '{mode}'")


if __name__ == "__main__":
    main()