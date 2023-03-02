"""Artifcial classes for pytest."""

from datetime import datetime, timedelta


class Box():
    """Generic Box class that represents an ouput or input transaction."""
    def __init__(self, address):
        self.address = address

    def as_dict(self):
        """Gets Box dict."""
        return {
            "address": self.address,
            "date": datetime.now() + timedelta(hours=36),
            "value": 10000,
            "script_type": "nulldata",
            "script": '4a4b4c'
        }


class Transaction():
    """Generic Transaction class that has inputs and outputs."""
    def __init__(self, inputs, outputs):
        self.inputs = inputs
        self.outputs = outputs

    def as_dict(self):
        """Gets Transaction dict."""
        return {
            "inputs": [i.as_dict() for i in self.inputs],
            "outputs": [o.as_dict() for o in self.outputs],
            "date": datetime.now() + timedelta(hours=36),
            "status": "confirmed"
        }


class Service():
    """Generic Service class that returns transactions."""
    def __init__(self, network):
        del network

    def gettransactions(self, address, after_txid, limit):
        """Gets list of transaction ids."""
        del address, after_txid, limit
        return ["a_good", "a_bad"]

    def gettransaction(self, txid):
        """Gets transaction info from transaction id."""
        del txid
        return Transaction(inputs=[Box("test")],
                           outputs=[Box(VAULT_BTC_WALLET_ADDRESS)])


class Wallet():
    """Generic Wallet class for testing."""
    def __init__(self, wallet_id, keys, network, db_uri):
        del wallet_id, keys, network, db_uri

    def scan(self):
        """Returns empty scan."""
        return {}


def wallet_create_or_open(wallet_id, keys, network, db_uri=None):
    """Generic method to create generic Wallet."""
    return Wallet(wallet_id, keys, network, db_uri)
