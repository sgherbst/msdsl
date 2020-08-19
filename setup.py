import os
from setuptools import setup, find_packages

name = 'msdsl'
version = '0.3.2'

DESCRIPTION = '''\
Library for generating synthesizable mixed-signal models for FPGA emulation\
'''

with open('README.md', 'r') as fh:
    LONG_DESCRIPTION = fh.read()

install_requires = [
    'svreal>=0.2.5',
    'scipy',
    'numpy',
    'matplotlib'
]
if os.name != 'nt':
    install_requires.append('cvxpy')

setup(
    name=name,
    version=version,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    keywords = ['analog', 'mixed-signal', 'mixed signal', 'behavioral',
                'real number model', 'real number models', 'rnm', 'rnms',
                'model', 'models', 'generator', 'verilog', 'system-verilog',
                'system verilog', 'synthesizable', 'emulation', 'fpga'],
    packages=find_packages(),
    install_requires=install_requires,
    license='MIT',
    url=f'https://github.com/sgherbst/{name}',
    author='Steven Herbst',
    author_email='sgherbst@gmail.com',
    python_requires='>=3.7',
    download_url = f'https://github.com/sgherbst/{name}/archive/v{version}.tar.gz',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'License :: OSI Approved :: MIT License',
        f'Programming Language :: Python :: 3.7'
    ],
    include_package_data=True,
    zip_safe=False
)
