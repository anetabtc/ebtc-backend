"""Setup script."""
from setuptools import find_packages, setup

setup(name="aneta_backend_v2",
      version="0.1.2",
      packages=find_packages(include=["server", "server.*"]),
      install_requires=[
          "Bootstrap-Flask==2.0.0", "Flask==2.0.2", "Flask-Testing==0.8.1",
          "Flask-WTF==1.0.0", "redis==4.1.1", "rq~=1.9.0", "bitcoinlib==0.6.7",
          "flask-cors==3.0.10", "requests~=2.28.1", "pytz==2022.7.1",
          "numpy>=1.22.3", "pytest", "pyyaml", "pylint==2.14.5", "types-PyYAML"
      ],
      include_package_data=True,
      extras_require={
          "develop": [
              "pytest-cov>=2.12.1",
              "pytest-pylint>=0.18.0",
              "yapf==0.32.0",
              "docformatter",
              "isort",
              "mypy@git+https://github.com/python/mypy.git@9bd651758e8ea2494" +
              "837814092af70f8d9e6f7a1",
          ]
      })
