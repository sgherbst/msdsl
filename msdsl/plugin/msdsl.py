import os
from pathlib import Path
from argparse import ArgumentParser

from svreal import get_svreal_header

# path to the top-level msdsl package directory
PACK_DIR = Path(__file__).resolve().parent.parent

# TODO: figure out how to remove dependency on anasymod (which itself depends on msdsl)
from anasymod.sources import VerilogHeader, VerilogSource
from anasymod.defines import Define
from anasymod.files import mkdir_p, rm_rf, which
from anasymod.util import call
from anasymod.plugins import Plugin
from anasymod.config import EmuConfig

class CustomPlugin(Plugin):
    def __init__(self, prj_cfg: EmuConfig, cfg_file, prj_root):
        super().__init__(cfg_file=cfg_file, prj_root=prj_root, build_root=os.path.join(prj_cfg.build_root_base, 'models'), name='msdsl')

        self.include_statements += ['`include "msdsl.sv"']

        # Parse command line arguments specific to MSDSL
        self.args = None
        self._parse_args()

        # Initialize Parameters
        self.dt = prj_cfg.cfg.dt

        # Initialize msdsl config
        self.cfg.model_dir = self._build_root

        # Update msdsl config with msdsl section in config file
        self.cfg.update_config(subsection=self._name)

        # Add defines according to command line arguments
        if self.args.float:
            self.add_define(Define(name='FLOAT_REAL', fileset='sim'))
        if self.args.range_assertions:
            self.add_define(Define(name='RANGE_ASSERTIONS', fileset='sim'))
        if self.args.add_saturation:
            self.add_define(Define(name='ADD_SATURATION'))

        ###############################################################
        # Execute actions according to command line arguments
        ###############################################################

        # make models
        if self.args.models:
            self.models()

##### Functions exposed for user to exercise on Analysis Object

    def models(self):
        """
        Call gen.py to generate analog models.
        """
        # make model directory, removing the old one if necessary
        rm_rf(self.cfg.model_dir)
        mkdir_p(self.cfg.model_dir)

        # run generator script
        gen_script = os.path.join(self._prj_root, 'gen.py')

        if 'PYTHON_MSDSL' in os.environ:
            python_name = os.environ['PYTHON_MSDSL']
        else:
            python_name = which('python')
            
        call([python_name, gen_script, '-o', self.cfg.model_dir, '--dt', str(self.dt)])

##### Utility Functions

    def _setup_defines(self):
        """
        Add Define objects that are specific to MSDSL
        """
        self.add_define(Define(name='DT_MSDSL', value=self.dt))
        self.add_define(Define(name='SIMULATION_MODE_MSDSL', fileset='sim'))

    def _setup_sources(self):
        """
        Add Source objects that are specific to MSDSL
        """

        # Add MSDSL and SVREAL sources
        self.add_source(source=VerilogHeader(files=[PACK_DIR / 'msdsl.sv'], config_path=self._srccfg_path))
        self.add_source(source=VerilogHeader(files=[get_svreal_header()], config_path=self._srccfg_path))

        # Add model sources
        self.add_source(source=VerilogSource(files=os.path.join(self.cfg.model_dir, '*.sv'), config_path=self._srccfg_path))

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view

        --range_assertions: Enables range checks, to detect overflows when working with fixed-point datatypes.
            To work with this feature efficiently, make sure to have --float set as well.

        --float: Change from fixed-point datatypes to float for running generated models.

        --add_saturation: Enable saturation feature for fixed-point based simulations. This will prevent overflows.

        --models: Generate functional models for selected project.

        """
        parser = ArgumentParser()
        parser.add_argument('--range_assertions', action='store_true')
        parser.add_argument('--float', action='store_true')
        parser.add_argument('--add_saturation', action='store_true')
        parser.add_argument('--models', action='store_true')

        self.args, _ = parser.parse_known_args()
