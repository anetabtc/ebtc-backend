# aneta_backend_v1.2

Example of how to handle background processes with Flask, Redis Queue, and Docker

### Quick Start
Install requirements:

```sh
$ pip install -e .
```

Or install developer requirements:

```sh
$ pip install -e . "develop"
```

Spin up the containers:

```sh
$ docker build -t web .
$ docker-compose up -d --build
```

Or run local:

```sh
$ python server/backend.py --local True
```

## Instructions For Testing
* For security reasons a few important files were taken out and all environment variables were removed. These are need to be added back to the repository before emulating our backend these files are:
    * config.ini
    * anetabtc-tool-0.1.jar
    * providers.json
* For the necessary ENVIRONMENT Variables:
    * VAULT_ERG_WALLET_ADDRESS
    * VAULT_BTC_WALLET_ADDRESS
    * VAULT_BTC_WALLET_ID
    * VAULT_BTC_WALLET_MNEMONIC
    * TOKEN_ID
    * SMART_CONTRACT_ERG_ADDRESS
    * ERGO_API
    * NETWORK
    * DB_URI
* The Aneta smart contracts compiled jar needs can be built here: https://github.com/anetabtc/aneta_contracts
* Feel free to contact <info@anetabtc.io> for further questions on installation and setup.

## Instructions For Contributing
* You can't push directly to master. Make a new branch in this repository (don't use a fork, since that will not properly trigger the checks when you make a PR). When your code is ready for review, make a PR and request reviews from the appropriate people.
* To merge a PR, you need at least one approval, and you have to pass the 4 checks defined in `.github/workflows/aneta.yml`, which you can run locally individually as follows:
    * `pytest -s tests/ --cov-config=.coveragerc --cov=server/ --cov-fail-under=100 --cov-report=term-missing:skip-covered`
    * `bash run_autoformat.sh`
    * `pytest . --pylint -m pylint --pylint-rcfile=.aneta_pylintrc`
* The first one is the unit testing check, which verifies that unit tests pass and that code is adequately covered. The "100" means that all lines in every file must be covered.
* The third one is the linter check, which runs Pylint with the custom config file `.aneta_pylintrc` in the root of this repository. Feel free to edit this file as necessary.
* The fourth one is the autoformatting check, which uses the custom config files `.style.yapf` and `.isort.cfg` in the root of this repository.
# anetabtc_backend_v1.2
