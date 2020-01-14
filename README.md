**NOTE**: Please check out the **v1** branch for the latest work.  These updates will be merged into the master branch soon, coinciding with a release on PyPI.

---

# Introduction

**msdsl** is a Python3 package for generating synthesizable real number models (RNMs) from analog circuits.  

# Installation

1. Open a terminal, and note the current directory, since the **pip** command below will clone some code from GitHub and place it in a subdirectory called **src**.  If you prefer to place the cloned code in a different directory, you can specify that by providing the **--src** flag to **pip**.
2. Install **msdsl** with **pip**:
```shell
> pip install -e git+https://github.com/sgherbst/msdsl.git#egg=msdsl
```

If you get a permissions error when running the **pip** command, you can try adding the **--user** flag.  This will cause **pip** to install packages in your user directory rather than to a system-wide location.
