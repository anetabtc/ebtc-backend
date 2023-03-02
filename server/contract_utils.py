"""Utilities for running our jar file for ergo operations."""

import datetime
import time
from subprocess import PIPE, Popen

import pytz
import requests

base_com = ['java', '-jar', 'anetabtc-tool-0.1.jar']
max_timesteps = 1000
UTC_TZ = pytz.utc


def check_box_confirmation(box_id: str):
    """Checks information for a given box_id."""
    try:
        response = requests.get(
            f'https://api.ergoplatform.com/api/v1/boxes/{box_id}',
            stream=True,
            timeout=5)
    except Exception as e:  # pragma: no cover
        print("IMPORTANT:", str(e))
        return False
    else:
        if response.status_code == 200:
            return True

    return False


def wrap_jar(*args):
    """Wraps our jar with exception catching."""
    process = Popen(base_com + list(args), stdout=PIPE, stderr=PIPE, text=True)
    out, err = process.communicate()
    return err if out is None else out


def run_contracts():
    """Runs contracts in our jar."""
    return wrap_jar('contracts')


def run_get_tokens_amount(address: str):
    """Get amount of tokens in our smart contract using jar."""
    return wrap_jar('getTokensAmount', str(address))


def run_verify(address: str, amount):  # pragma: no cover
    """Creates verification box for smart contract."""
    print("IMPORTANT: Time verify started: " +
          str(datetime.datetime.now().astimezone(UTC_TZ)))
    vbox = wrap_jar('verify', str(address), str(amount)).lower()
    vbox = vbox[:-1]
    print("IMPORTANT: ", vbox, '(contract utils)')

    if len(vbox) != 64:
        return False, vbox

    t = 0
    print("IMPORTANT: Time verify created: " +
          str(datetime.datetime.now().astimezone(UTC_TZ)))
    while not check_box_confirmation(vbox) and t <= max_timesteps:
        t += 1
        time.sleep(30)

    print("IMPORTANT: Time verify ended: " +
          str(datetime.datetime.now().astimezone(UTC_TZ)))
    return check_box_confirmation(vbox), vbox


def run_mint(address, amount, verify_box_id):  # pragma: no cover
    """Runs mint smart contract."""
    tx_id = wrap_jar('mint', str(address), str(amount), str(verify_box_id))
    print("IMPORTANT: mint_tx_id - " + tx_id)
    if len(tx_id) != 67:
        return False, tx_id

    return True, tx_id[1:-2]
