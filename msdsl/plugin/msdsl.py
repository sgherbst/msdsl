import os
from pathlib import Path
from argparse import ArgumentParser

from svreal import get_svreal_header

# path to the top-level msdsl package directory
PACK_DIR = Path(__file__).resolve().parent.parent

# TODO: figure out how to remove dependency on anasymod (which itself depends on msdsl)
from anasymod.sources import VerilogHeader, VerilogSource, FunctionalModel
from anasymod.defines import Define
from anasymod.files import mkdir_p, rm_rf, which
from anasymod.util import call
from anasymod.plugins import Plugin
from anasymod.config import EmuConfig

class CustomPlugin(Plugin):
    def __init__(self, prj_cfg: EmuConfig, cfg_file, prj_root):
        super().__init__(cfg_file=cfg_file, prj_root=prj_root, build_root=prj_cfg.build_root_functional_models, name='msdsl')

        self.include_statements += ['`include "msdsl.sv"']

        # Initialize list of functional models to be generated
        self.generator_sources = []

        # Initialize Parameters
        self.dt = prj_cfg.cfg.dt

        # Update msdsl config with msdsl section in config file
        self.cfg.update_config(subsection=self._name)

##### Custom functions for actions triggered from command line or by setting an option

    def models(self):
        """
        Call gen.py to generate analog models.
        """
        # make model directory, removing the old model directory if necessary
        rm_rf(self._build_root)

        # run generator script
        if 'PYTHON_MSDSL' in os.environ:
            python_name = os.environ['PYTHON_MSDSL']
        else:
            python_name = which('python')
        for generator_source in self.generator_sources:
            # make model directory if necessary
            mkdir_p(os.path.join(self._build_root, generator_source.fileset, generator_source.name))
            for file in generator_source.files:
                call([python_name, file, '-o', os.path.join(self._build_root, generator_source.fileset, generator_source.name), '--dt', str(self.dt)])

    def float(self):
        self._add_define(Define(name='FLOAT_REAL', fileset='sim'))

    def range_assertions(self):
        self._add_define(Define(name='RANGE_ASSERTIONS', fileset='sim'))

    def add_saturation(self):
        self._add_define(Define(name='ADD_SATURATION'))

##### Utility Functions

    def _setup_defines(self):
        """
        Add Define objects that are specific to MSDSL
        """
        self._add_define(Define(name='DT_MSDSL', value=self.dt))
        self._add_define(Define(name='SIMULATION_MODE_MSDSL', fileset='sim'))

    def _setup_sources(self):
        """
        Add Source objects that are specific to MSDSL
        """

        # Add MSDSL and SVREAL sources
        self._add_source(source=VerilogHeader(files=[PACK_DIR / 'msdsl.sv'],
                                              config_path=self._srccfg_path,
                                              name='msdsl'))
        self._add_source(source=VerilogHeader(files=[get_svreal_header()],
                                              config_path=self._srccfg_path,
                                              name='svreal'))

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view

        --range_assertions: Enables range checks, to detect overflows when working with fixed-point datatypes.
            To work with this feature efficiently, make sure to have --float set as well.

        --float: Change from fixed-point datatypes to float for running generated models.

        --add_saturation: Enable saturation feature for fixed-point based simulations. This will prevent overflows.

        """
        parser = ArgumentParser()
        parser.add_argument('--range_assertions', action='store_true')
        parser.add_argument('--float', action='store_true')
        parser.add_argument('--add_saturation', action='store_true')

        self.args, _ = parser.parse_known_args()