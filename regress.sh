# upgrade pip
python -m pip install --upgrade pip

# install HardFloat
curl -L https://git.io/JJ5YF > install_hardfloat.sh
source install_hardfloat.sh

# install various python dependencies
pip install wheel
pip install pytest pytest-cov

# temporary fix
pip install cvxpy==1.1.7

# install msdsl
pip install -e .

# install magma ecosystem
# a specific version of pysmt is used to avoid cluttering the output with warnings
pip install pysmt==0.9.0
pip install fault==3.0.36 magma-lang==2.1.17 coreir==2.0.120 mantle==2.0.10 hwtypes==1.4.3 ast_tools==0.0.30 kratos==0.0.31.1

# run tests
pytest --cov-report=xml --cov=msdsl tests/ -v -r s

# upload coverage information
curl -s https://codecov.io/bash | bash
