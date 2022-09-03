Adsorption File Parser
======================

A pure python parser to sorption files from various instrumentation manufacturers.
It comes with minimal dependencies and maximum flexibility.

Currently supports:

    - Micromeritics
    - Surface Measurement Systems DVS
    - 3P instruments
    - Quantachrome
    - MicrotracBEL

.. start-badges

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    * - status
      - | |status| |commits-since|
    * - license
      - | |license|
    * - tests
      - | |GHA| |codecov|
        | |requires|
    * - package
      - | |version| |wheel|
        | |supported-versions| |supported-implementations|

.. |status| image:: https://www.repostatus.org/badges/latest/active.svg
    :target: https://www.repostatus.org/#active
    :alt: Project Status: Active – The project has reached a stable, usable state and is being actively developed.

.. |commits-since| image:: https://img.shields.io/github/commits-since/AIF-development-team/adsorption-file-parser/latest/develop
    :alt: Commits since latest release
    :target: https://github.com/AIF-development-team/adsorption-file-parser/compare/master...develop

.. |license| image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://opensource.org/licenses/MIT
    :alt: Project License

.. |GHA| image:: https://github.com/AIF-development-team/adsorption-file-parser/workflows/CI/badge.svg
    :alt: GHA-CI Build Status
    :target: https://github.com/AIF-development-team/adsorption-file-parser/actions

.. |requires| image:: https://requires.io/github/AIF-development-team/adsorption-file-parser/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/AIF-development-team/adsorption-file-parser/requirements/?branch=master

.. |codecov| image:: https://img.shields.io/codecov/c/github/AIF-development-team/adsorption-file-parser.svg
    :alt: Coverage Status
    :target: https://codecov.io/gh/AIF-development-team/adsorption-file-parser

.. |version| image:: https://img.shields.io/pypi/v/adsorption-file-parser/.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/adsorption-file-parser/

.. |wheel| image:: https://img.shields.io/pypi/wheel/adsorption-file-parser/.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/adsorption-file-parser/

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/adsorption-file-parser/.svg
    :alt: Supported versions
    :target: https://pypi.org/project/adsorption-file-parser/

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/adsorption-file-parser/.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/adsorption-file-parser/

.. end-badges


Installation
============

Install using pip

.. code:: bash

    pip install adsorption-file-parser


Documentation
=============

.. code:: bash

    from adsorption_file_parser import read
    meta, data = read(
        path="path/to/file",
        manufacturer="manufacturer",
        fmt="supported format"
    )

Bugs or questions?
==================

For any bugs found or feature requests, please open an
`issue <https://github.com/AIF-development-team/adsorption-file-parser/issues/>`__
or, even better, submit a
`pull request <https://github.com/AIF-development-team/adsorption-file-parser/pulls/>`__.
