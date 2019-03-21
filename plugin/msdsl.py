import os

from anasymod.sources import Sources, VerilogHeader, VerilogSource, VHDLSource
from anasymod.defines import Define
from anasymod.files import mkdir_p, rm_rf, get_from_module, which
from argparse import ArgumentParser
from anasymod.util import call
from anasymod.plugins import Plugin

class CustomPlugin(Plugin):
    def __init__(self, cfg_file, prj_root, build_root):
        super().__init__(cfg_file=cfg_file, prj_root=prj_root, build_root=build_root, name='msdsl')

        # Parse command line arguments specific to MSDSL
        self.args = None
        self._parse_args()

        # Initialize msdsl config
        self.cfg.dt = 0.1e-6
        self.cfg.model_dir = os.path.join(self._build_root, 'models')

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
        call([which('python'), gen_script, '-o', self.cfg.model_dir, '--dt', str(self.cfg.dt)])

##### Utility Functions

    def _setup_defines(self):
        """
        Add Define objects that are specific to MSDSL
        """
        self._set_dt()
        self.add_define(Define(name='SIMULATION_MODE_MSDSL', fileset='sim'))
        self.add_define(Define(name='OFF_BITS_MSDSL', value=32))

    def _set_dt(self):
        self.add_define(Define(name='DT_MSDSL', value=self.cfg.dt))

    def _setup_sources(self):
        """
        Add Source objects that are specific to MSDSL
        """

        # Add MSDSL and SVREAL sources
        self.add_source(source=VerilogSource(files=get_from_module('msdsl', 'src', '*.sv'), config_path=self._srccfg_path))
        self.add_source(source=VerilogHeader(files=get_from_module('msdsl', 'include', '*.sv'), config_path=self._srccfg_path))

        self.add_source(source=VerilogSource(files=get_from_module('svreal', 'src', '*.sv'), config_path=self._srccfg_path))
        self.add_source(source=VerilogHeader(files=get_from_module('svreal', 'include', '*.sv'), config_path=self._srccfg_path))

        # Add model sources
        self.add_source(source=VerilogSource(files=os.path.join(self.cfg.model_dir, '*.sv'), config_path=self._srccfg_path))

    def _parse_args(self):
        """
        Read command line arguments. This supports convenient usage from command shell e.g.:
        python analysis.py -i filter --models --sim --view
        """
        parser = ArgumentParser()
        parser.add_argument('--range_assertions', action='store_true')
        parser.add_argument('--float', action='store_true')
        parser.add_argument('--add_saturation', action='store_true')
        parser.add_argument('--models', action='store_true')

        self.args, _ = parser.parse_known_args()