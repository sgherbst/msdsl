# upgrade pip
python -m pip install --upgrade pip

# install HardFloat
curl -L https://git.io/JJ5YF > install_hardfloat.sh
source install_hardfloat.sh

# get S4P data
curl -L https://git.io/JtNrY > peters_01_0605_B1_thru.s4p
curl -L https://git.io/JqceS > channel_resp_mar11.csv

# install various python dependencies
pip install wheel
pip install pytest

# install msdsl
pip install -e .

# install svtb, which stands in for fault and magma: they do not install on current Python
pip install svtb

# run tests
pytest tests/ -v -r s
