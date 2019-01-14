from setuptools import setup, find_packages

setup(
    name='msdsl',
    version='0.0.1',
    description='Library for describing mixed-signal circuits for emulation',
    url='https://github.com/sgherbst/msdsl',
    author='Steven Herbst',
    author_email='sherbst@stanford.edu',
    packages=['msdsl'],
    install_requires=[
        'scipy',
        'numpy',
        'matplotlib'
    ],
    include_package_data=True,
    zip_safe=False,
)
