"""AnetaBackend v1.2."""

import argparse
import logging
import multiprocessing
import os
import time
from datetime import datetime, timedelta
from decimal import ROUND_DOWN, Decimal
from multiprocessing import Process
from random import randint
from time import sleep

import pytz
import requests
import urllib3
from pytz import timezone

try:  # pragma: no cover
    import contract_utils as ctrs  # pylint: disable=import-error
    from bitcoinlib.services.services import Service
    from bitcoinlib.wallets import wallet_create_or_open
    PYTEST = False
except ImportError:
    from aneta_backend_v2.tests.pytest_helpers import *  # pylint: disable=wildcard-import
    PYTEST = True

# IMPORTANT PARAMETERS from ENV Variables
VAULT_ERG_WALLET_ADDRESS = os.getenv('VAULT_ERG_WALLET_ADDRESS')
VAULT_BTC_WALLET_ADDRESS = os.getenv('VAULT_BTC_WALLET_ADDRESS')
VAULT_BTC_WALLET_ID = os.getenv('VAULT_BTC_WALLET_ID')
VAULT_BTC_WALLET_MNEMONIC = os.getenv('VAULT_BTC_WALLET_MNEMONIC')
TOKEN_ID = os.getenv('TOKEN_ID')
SMART_CONTRACT_ERG_ADDRESS = os.getenv('SMART_CONTRACT_ERG_ADDRESS')
ERGO_API = os.getenv('ERGO_API')
NETWORK = os.getenv('NETWORK')

DB_URI = os.getenv('DB_URI')

if not PYTEST:  # pragma: no cover
    for VAR in [
            VAULT_ERG_WALLET_ADDRESS, VAULT_BTC_WALLET_ADDRESS,
            VAULT_BTC_WALLET_ID, VAULT_BTC_WALLET_MNEMONIC, TOKEN_ID,
            SMART_CONTRACT_ERG_ADDRESS
    ]:
        if VAR is None:
            raise Exception("Important ENV Variable was not found")
    print("Succesfully loaded ENV vars.")

MAX_TIMESTEPS = 2
REQUEST_RATE = 300  # sec
MAX_QUEUE_TIME = 1  # hr

try:  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("-local",
                        "--local",
                        action='store_true',
                        help="Local Run")
    args = parser.parse_args()
except SystemExit:

    class Args():
        """Generic Args instead of parser."""
        local = True

    args = Args

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
UTC_TZ = pytz.utc
EST_TZ = timezone('US/Eastern')

sleep(randint(1, 7))

if not args.local:  # pragma: no cover
    db_uri = DB_URI
    os.system("cp providers.json /root/.bitcoinlib/providers.json")
    os.system("cp config.ini /root/.bitcoinlib/config.ini")
    w = wallet_create_or_open(VAULT_BTC_WALLET_ID,
                              keys=VAULT_BTC_WALLET_MNEMONIC,
                              network=NETWORK,
                              db_uri=db_uri)
else:
    w = wallet_create_or_open(VAULT_BTC_WALLET_ID,
                              keys=VAULT_BTC_WALLET_MNEMONIC,
                              network=NETWORK)

ergoAPI = ERGO_API

print("I am running ", str(randint(2, 10)))

sleep(randint(2, 10))
w.scan()


class AnetaBackendNode:
    """AnetaBackendNode that peforms both minting and redeeming, and manages
    internal queues."""
    def __init__(self, hex_symbol, epoch_delay=10):
        self.epoch_delay = epoch_delay
        self.start_time = datetime.now().astimezone(UTC_TZ)

        # Internal queue to keep track of pending orders.
        self.mint_queue = []
        self.redeem_queue = []
        self.mint_queue_time = {}
        self.redeem_queue_time = {}

        # Internal database of done transactions.
        self.mint_db = set()
        self.mint_finished = set()
        self.redeem_db = set()
        self.redeem_finished = set()

        self.last_tx = ''

        self.hex_symbol = hex_symbol

        # Initialize logging.
        date_time = datetime.now().strftime("%m-%d-%Y_%H:%M:%S")
        utc_date_time = datetime.now().astimezone(UTC_TZ).strftime(
            "%m-%d-%Y_%H:%M:%S")
        logging.basicConfig(filename='./logs/server_run_' + date_time + '_' +
                            hex_symbol + '.log',
                            level=logging.INFO)
        logging.info('Initiating file with {} time {} utc time'.format(
            date_time, utc_date_time))
        logging.info("Number of cpu : {}".format(multiprocessing.cpu_count()))

    def get_btc_tx_info(self, tx_id, network=NETWORK):
        """Gets BTC transaction information using transaction id."""
        try:
            srv = Service(network=network)
            transaction = srv.gettransaction(tx_id)
            sender = transaction.inputs[0].address
            logging.info("Checking outputs for {}".format(str(tx_id)))
            # For all outputs try to find transaction with OP_RETURN
            for output in transaction.outputs:
                logging.info("Output to {}".format(str(output.address)))
                receiver = output.address
                if transaction.as_dict()['date'] is not None:
                    if receiver == VAULT_BTC_WALLET_ADDRESS:
                        tx_time = UTC_TZ.localize(
                            transaction.as_dict()['date'])
                        amount = int(output.as_dict()['value']) / 100000000
                        if transaction.as_dict()['status'] == 'confirmed':
                            logging.info("Confirmed payement to {}".format(
                                str(output.address)))
                            for output in transaction.outputs:
                                if output.as_dict(
                                )['script_type'] == 'nulldata':
                                    op_return = bytes.fromhex(
                                        output.as_dict()['script']).decode(
                                            'utf-8')[2:]
                                    logging.info(
                                        "Found info OP_RETURN {}".format(
                                            str(op_return)))
                                    return sender, amount, receiver, tx_time, op_return, True
                            # No OP_RETURN Metadata.
                            logging.info(
                                "Could not find OP_RETURN for tx_id {}".format(
                                    str(transaction)))  # pragma: no cover
                        else:
                            # Transaction is not confirmed yet.
                            logging.info(
                                "Transaction {} is not confirmed".format(
                                    str(transaction)))  # pragma: no cover
            logging.info("OP_RETURN Transaction not found")  # pragma: no cover
            return None, None, None, None, None, False  # pragma: no cover
        except Exception as e:  # pragma: no cover
            logging.info("bitcoinlib had error {}".format(str(e)))
        return None, None, None, None, None, False  # pragma: no cover

    def mint(self, erg_wallet_addr, amount):  # pragma: no cover
        """Mints eBTC to user ERG wallet address."""
        ## Run Verify and Minting Smart Contract
        logging.info("Starting mint to {} amount {}".format(
            str(erg_wallet_addr), str(amount)))
        try:
            if None in [amount, erg_wallet_addr]:
                raise Exception("amount or wallet address is wrong")
            amount = Decimal(amount).quantize(Decimal('.0000001'),
                                              rounding=ROUND_DOWN)
            if amount.as_tuple().exponent < -8:
                raise Exception(
                    f"amount can not be more that 8 decimals, for {amount}")
            ebtc = int(int(amount * 100000000) *
                       0.995) - 10000  # 0.0001 and 0.5% for bridge fee
            verify_succeed, vbox = ctrs.run_verify(address=erg_wallet_addr,
                                                   amount=ebtc)
            logging.info("Verified Transaction for Mint")
            if verify_succeed:
                logging.info("Mint {} amount {} vbox {}".format(
                    str(erg_wallet_addr), str(ebtc), str(vbox)))
                mint_succeed, mint_tx = ctrs.run_mint(address=erg_wallet_addr,
                                                      amount=ebtc,
                                                      verify_box_id=vbox)
                if not mint_succeed:
                    # Minting did not succeed.
                    raise Exception(mint_tx)
                # Success!
                logging.info("vbox: {}".format(vbox))
                logging.info("mint_tx: {}".format(mint_tx))
                logging.info("Minting Sucess!")
                return True
            # Transaction was not sucessfully verified.
            raise Exception("Mint transaction was not verified.")
        except Exception as e:
            logging.info("Mint Failed with error {}".format(str(e)))
            return False

    def execute_mint(self, num_executions=1):
        """Pops from minting queue and executes mints."""
        for _ in range(num_executions):
            if len(self.mint_queue) > 0:
                tx_id = self.mint_queue.pop(0)
                logging.info("Processing Mint {} Started".format(str(tx_id)))
                try:
                    # Get Transaction Info and Execute Minting
                    _, amount, _, _, op_return, check_transaction = self.get_btc_tx_info(
                        tx_id)
                    logging.info("Returning Mint info {}".format(
                        str(check_transaction)))
                    if check_transaction:  # pragma: no cover
                        if self.mint(erg_wallet_addr=op_return, amount=amount):
                            logging.info(
                                "Adding Succesful Mint to finished set")
                            self.mint_finished.add(tx_id)
                            logging.info("Processing Mint {} Finished".format(
                                str(tx_id)))
                            return
                    if self.mint_queue_time[tx_id] + timedelta(
                            hours=MAX_QUEUE_TIME) > datetime.now().astimezone(
                                UTC_TZ):
                        logging.info("Failed Mint Requeuing {}".format(
                            str(tx_id)))
                        self.mint_queue.append(tx_id)
                    else:  # pragma: no cover
                        logging.info("Unable to Mint {}".format(str(tx_id)))
                except Exception as e:  # pragma: no cover
                    logging.info("Error - {}".format(str(e)))
                    logging.info("Failed Mint Requeuing {}".format(str(tx_id)))
                    self.mint_queue.append(tx_id)
                logging.info("Processing Mint {} Finished".format(str(tx_id)))

    def update_mint_queue(self, network=NETWORK):
        """Adds transactions from block explorer to mint queue."""
        try:
            srv = Service(network=network)
            transactions = srv.gettransactions(VAULT_BTC_WALLET_ADDRESS,
                                               after_txid=self.last_tx,
                                               limit=10000)
            for transaction in transactions:
                try:
                    tx_id = str(transaction)
                    tx_time = UTC_TZ.localize(
                        srv.gettransaction(tx_id).as_dict()['date'])
                    # logging.info(str(tx_time) + " {}".format(str(tx_id) + " start_time: {}".format(str(self.start_time))
                    if tx_id[0] == self.hex_symbol:
                        if srv.gettransaction(tx_id).as_dict(
                        )['inputs'][0]['address'] != VAULT_BTC_WALLET_ADDRESS:
                            if tx_id not in self.mint_db and tx_time >= self.start_time:  # - timedelta(hours = 36)
                                logging.info("Queued tx: {} {}".format(
                                    str(tx_time), str(tx_id)))
                                self.mint_queue.append(tx_id)
                                self.mint_queue_time[tx_id] = datetime.now(
                                ).astimezone(UTC_TZ)
                            self.mint_db.add(tx_id)
                except Exception as e:  # pragma: no cover
                    logging.info("Error adding to Mint Queue {}".format(
                        str(e)))
            logging.info("Transactions in Mint Queue {} ".format(
                str(len(self.mint_queue))))
        except Exception as e:  # pragma: no cover
            logging.info("Error Failed to Update Mint Queue - {}".format(
                str(e)))

    def get_erg_tx_info(self, tx_id):
        """Gets ERG transaction information using transaction id."""
        api = ergoAPI + "transactions/"  # explorer api
        t = 0
        while t <= MAX_TIMESTEPS:
            logging.info("Checking API {}".format(api + tx_id))
            response = requests.get(api + tx_id)
            if response.status_code == 200:
                sender = response.json()['inputs'][0]['address']
                # Check outputs to find R4 transaction
                for output in response.json()['outputs']:
                    if output[
                            'address'] == VAULT_ERG_WALLET_ADDRESS:  # pragma: no cover
                        receiver = output['address']
                        for asset in output['assets']:
                            try:
                                if asset['tokenId'] == TOKEN_ID:
                                    amount = asset['amount']
                                    tx_time = EST_TZ.localize(
                                        datetime.fromtimestamp(
                                            response.json()['timestamp'] /
                                            1000))
                                    for output in response.json()['outputs']:
                                        try:
                                            logging.info(
                                                "Checking for BTC metadata: {}"
                                                .format(
                                                    str(output['transactionId']
                                                        )))
                                            if output[
                                                    'address'] == VAULT_ERG_WALLET_ADDRESS:
                                                btc_metadata = str(
                                                    bytes.
                                                    fromhex(output[
                                                        'additionalRegisters']
                                                            ['R4']
                                                            ['serializedValue']
                                                            ).decode(
                                                                'utf-8'))[2:]
                                                return sender, amount, receiver, tx_time, btc_metadata, True
                                            raise Exception(
                                                "No eBTC in Transaction")
                                        except Exception as e:
                                            logging.info(
                                                "BTC address not in R4 register {} error {}"
                                                .format(
                                                    str(output['transactionId']
                                                        ), str(e)))
                            except Exception as e:
                                logging.info(
                                    "Error with finding TokenId {}".format(
                                        str(e)))
                        logging.info("No eBTC in Transaction {}".format(
                            str(output['transactionId'])))
                logging.info("Found transaction but BTC metadata not found")
                return None, None, None, None, None, False
            logging.info("Searching for ERG tx: {}".format(
                str(tx_id)))  # pragma: no cover
            t += 1  # pragma: no cover
            time.sleep(REQUEST_RATE)  # pragma: no cover
            logging.info("Something is wrong with tx {}".format(
                str(tx_id)))  # pragma: no cover
        logging.info("Verify Redeem Failed")  # pragma: no cover
        return None, None, None, None, None, False  # pragma: no cover

    def update_redeem_queue(self):  # pragma: no cover
        """Adds transactions from block explorer to redeem queue."""
        api = ergoAPI + f"addresses/{VAULT_ERG_WALLET_ADDRESS}/transactions/"  # explorer api
        logging.info("Checking API {}".format(api))
        try:
            response = requests.get(api)  # Need to get more than just 20 items
            erg_transactions = []
            if not PYTEST:
                for item in response.json()['items']:
                    erg_transactions.append(item)
            for transaction in erg_transactions:
                tx_id = str(transaction['id'])
                tx_time = EST_TZ.localize(
                    datetime.fromtimestamp(transaction['timestamp'] / 1000))
                # TODO Check if outgoing - putting eBTC mints here
                if tx_id[0] == self.hex_symbol:
                    if transaction['inputs'][0][
                            'address'] != VAULT_ERG_WALLET_ADDRESS:
                        if tx_id not in self.redeem_db and tx_time >= self.start_time:
                            logging.info("{} {}".format(
                                str(tx_time), str(tx_id)))
                            self.redeem_queue.append(tx_id)
                            self.redeem_queue_time[tx_id] = datetime.now(
                            ).astimezone(UTC_TZ)
                        self.redeem_db.add(tx_id)
            logging.info("Transactions in Redeem Queue {}".format(
                str(len(self.redeem_queue))))
        except Exception as e:
            logging.info("Error Failed to Update Redeem Queue - {}".format(
                str(e)))

    def redeem(self, btc_wallet_addr, amount):  # pragma: no cover
        """Redeems BTC to user BTC wallet address."""
        logging.info("IMPORTANT: addresses count - {}".format(
            str(len(w.addresslist()))))
        logging.info("IMPORTANT: Vault balance - {}".format(str(w.balance())))
        logging.info("Endpoint BTC address:{}".format(
            str(VAULT_BTC_WALLET_ADDRESS)))
        t = 0
        tx_id = None
        amount = int(
            int(amount) * 0.995) - 10000  # 0.0001 and 0.5% for bridge fee
        try:
            while t <= MAX_TIMESTEPS:
                tx_id = w.send_to(btc_wallet_addr,
                                  amount,
                                  fee=2000,
                                  offline=False)
                if tx_id:
                    logging.info("tx id: {}".format(str(tx_id)))
                    logging.info(
                        f"SUCCESS! Sent from {VAULT_BTC_WALLET_ADDRESS}  to {btc_wallet_addr} amount {amount}"
                    )
                    return True
                time.sleep(REQUEST_RATE)
                t += 1
        except Exception as e:
            logging.info(
                f"Failed to send from {VAULT_BTC_WALLET_ADDRESS} to {btc_wallet_addr} amount {amount}"
            )
            logging.info("Error - {}".format(str(e)))
        logging.info("Failed sending timed out")
        return False

    def execute_redeem(self, num_executions=1):  # pragma: no cover
        """Pops from redeem queue and executes redeem."""
        for _ in range(num_executions):
            if len(self.redeem_queue) > 0:
                tx_id = self.redeem_queue.pop(0)
                logging.info("Processing Redeem {} Started".format(str(tx_id)))
                try:
                    # Get Transaction Info and Execute Minting
                    _, amount, _, _, btc_metadata, verify_redeem = self.get_erg_tx_info(
                        tx_id)
                    logging.info("Redeem info {}".format(str(verify_redeem)))
                    if verify_redeem:
                        if self.redeem(btc_wallet_addr=btc_metadata,
                                       amount=amount):
                            logging.info(
                                "Adding Succesful Redeem to finished set")
                            self.redeem_finished.add(tx_id)
                            logging.info(
                                "Processing Redeem {} Finished".format(
                                    str(tx_id)))
                            return
                    if self.redeem_queue_time[tx_id] + timedelta(
                            hours=MAX_QUEUE_TIME) > datetime.now().astimezone(
                                UTC_TZ):
                        logging.info("Failed Redeem Requeuing {}".format(
                            str(tx_id)))
                        self.redeem_queue.append(tx_id)
                    else:
                        logging.info("Unable to Redeem {}".format(str(tx_id)))
                except Exception as e:
                    logging.info("Error - {}".format(str(e)))
                    logging.info("Failed Redeem Requeuing {}".format(
                        str(tx_id)))
                    self.redeem_queue.append(tx_id)
                logging.info("Processing Redeem {} Finished".format(
                    str(tx_id)))

    def run(self):
        """AnetaBackendNode Startup."""
        while True:
            logging.info("Time: {}".format(
                datetime.now().strftime("%m-%d-%Y_%H:%M:%S")))
            # # Read Minting Requests and Add to Queue
            self.update_mint_queue()
            # # Pop and Try to Complete Next Minting Request
            self.execute_mint()
            # Read Redeem Requests and Add to Queue
            self.update_redeem_queue()
            # Pop and Try to Complete Next Redeem Request
            self.execute_redeem()
            time.sleep(self.epoch_delay)
            if PYTEST:
                return


def run_thread(hex_symbol):
    """Main function on a thread that runs an AnetaBackendNode."""
    node = AnetaBackendNode(hex_symbol)
    node.run()


def start_multiple_threads(inputs, proccess):
    """Starts multiple threads on inputs."""
    procs = []

    # Instantiating process with arguments.
    for i in inputs:
        proc = Process(target=proccess, args=(i, ))
        procs.append(proc)
        proc.start()

    # Complete the processes.
    for proc in procs:
        proc.join()

    return True


if __name__ == "__main__":  # pragma: no cover
    # All hexadecimal symbols to run on each thread.
    thread_hexes = [
        'a', 'b', 'c', 'd', 'e', 'f', '0', '1', '2', '3', '4', '5', '6', '7',
        '8', '9'
    ]
    start_multiple_threads(thread_hexes, run_thread)
