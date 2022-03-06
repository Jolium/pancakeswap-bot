"""
https://github.com/manuelhb14/cake_uni_transaction_bot
"""
from web3 import Web3
from system.load_data import load_data

import json
import time
import sys


# bsc = "https://bsc-dataseed.binance.org/"
# web3 = Web3(Web3.HTTPProvider(bsc))
my_address = load_data('auth/auth.yml')['WALLET_ADDRESS']


def connect():
    try:
        w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))

    except Exception as e:
        print(f"Not a valid network...\nSupports only bsc-mainnet network\n{e}")
        sys.exit()
    return w3


def get_bnb_balance(wallet_address=my_address):
    w3 = connect()
    balance = w3.eth.getBalance(wallet_address)
    return w3.fromWei(balance, 'ether')


def get_token_balance(token, wallet_address=my_address):
    w3 = connect()

    token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
    get_token_abi = load_data('config/pancake.yml')['GET_TOKEN_ABI']

    token_checksum_address = w3.toChecksumAddress(token_address)
    token_contract = w3.eth.contract(token_checksum_address, abi=get_token_abi)

    balance = token_contract.functions.balanceOf(wallet_address).call()
    return w3.fromWei(balance, 'ether')


class TxnBot:
    def __init__(self, token, slippage=0.5, gas_price=5, wallet_address=my_address):
        self.w3 = connect()

        # self.address = load_data('auth/auth.yml')['WALLET_ADDRESS']
        self.address = wallet_address
        self.private_key = load_data('auth/auth.yml')['PRIVATE_KEY']

        token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
        self.token_address = Web3.toChecksumAddress(token_address)

        self.token_contract = self.set_token_contract()
        self.router_address, self.router = self.set_router()
        self.slippage = 1 - (slippage / 100)
        self.gas_price = Web3.toWei(gas_price, 'gwei')

        # print(f"Current balance of {self.token_contract.functions.symbol().call()}: "
        #       f"{Web3.fromWei(self.token_contract.functions.balanceOf(self.address).call(), 'ether')}")

    def set_router(self):
        pancakeswap_outer_contract_address = load_data('config/pancake.yml')['ROUTER_CONTRACT_ADDRESS']
        router_address = Web3.toChecksumAddress(pancakeswap_outer_contract_address)  # mainnet router
        with open("./abis/pancakeRouter.json") as f:
            contract_abi = json.load(f)['abi']
        router = self.w3.eth.contract(address=router_address, abi=contract_abi)

        return router_address, router

    def set_token_contract(self):
        token_address = Web3.toChecksumAddress(self.token_address)
        with open("./abis/bep20_abi_token.json") as f:
            contract_abi = json.load(f)
        token_contract = self.w3.eth.contract(address=token_address, abi=contract_abi)

        return token_contract

    def get_amounts_out_buy(self, quantity):
        buy = self.router.functions.getAmountsOut(
            int(Web3.toWei(quantity, 'ether') * self.slippage),
            [self.router.functions.WETH().call(), self.token_address]
        ).call()

        return buy

    def get_amounts_out_sell(self, quantity):
        sell = self.router.functions.getAmountsOut(
            int(Web3.toWei(quantity, 'ether') * self.slippage),
            [self.token_address, self.router.functions.WETH().call()]
        ).call()

        return sell

    def get_amounts_out_sell1(self):
        sell = self.router.functions.getAmountsOut(
            self.token_contract.functions.balanceOf(self.address).call(),
            [self.token_address, self.router.functions.WETH().call()]
        ).call()

        return sell

    def approve(self):
        txn_approve = self.token_contract.functions.approve(
            self.router_address,
            2 ** 256 - 1
        ).buildTransaction(
            {'from': self.address,
             'gas': 250000,
             'gasPrice': self.gas_price,
             'nonce': self.w3.eth.getTransactionCount(self.address),
             'value': 0}
        )

        signed_txn = self.w3.eth.account.sign_transaction(txn_approve, self.private_key)

        # txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        # print(f'approve: {txn.hex()}')
        # txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
        # print(txn_receipt)

        # Wait after approve 10 seconds before sending transaction
        time.sleep(10)

    def buy_token(self, quantity):
        txn = self.router.functions.swapExactETHForTokens(
            self.get_amounts_out_buy(quantity)[-1],
            [self.router.functions.WETH().call(), self.token_address],
            bytes.fromhex(self.address[2:]),
            int(time.time()) + 10 * 60  # 10 min limit
        ).buildTransaction(
            {'from': self.address,
             'gas': 250000,
             'gasPrice': self.gas_price,
             'nonce': self.w3.eth.getTransactionCount(self.address),
             'value': Web3.toWei(quantity, 'ether')}
        )

        signed_txn = self.w3.eth.account.sign_transaction(
            txn,
            self.private_key
        )

        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        # txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)

        return Web3.toHex(txn)

    def sell_token(self, quantity):
        self.approve()

        txn = self.router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
            Web3.toWei(quantity, 'ether'),
            0,
            [self.token_address, self.router.functions.WETH().call()],
            self.address,
            int(time.time()) + 10 * 60  # 10 min limit
        ).buildTransaction(
            {'from': self.address,
             'gas': 250000,
             'gasPrice': self.gas_price,
             'nonce': self.w3.eth.getTransactionCount(self.address)}
        )

        signed_txn = self.w3.eth.account.sign_transaction(
            txn,
            self.private_key
        )

        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        # print(f'sell txn: {txn.hex()}')
        # txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
        # print(txn_receipt)

        return Web3.toHex(txn)

    def sell_token_max(self):
        self.approve()

        txn = self.router.functions.swapExactTokensForETH(
            self.token_contract.functions.balanceOf(self.address).call(),
            int(self.get_amounts_out_sell1()[-1] * self.slippage),
            [self.token_address, self.router.functions.WETH().call()],
            bytes.fromhex(self.address[2:]),
            int(time.time()) + 10 * 60  # 10 min limit
        ).buildTransaction(
            {'from': self.address,
             'gas': 250000,
             'gasPrice': self.gas_price,
             'nonce': self.w3.eth.getTransactionCount(self.address),
             'value': 0}
        )

        signed_txn = self.w3.eth.account.sign_transaction(
            txn,
            self.private_key
        )

        txn = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        # print(txn.hex())
        # txn_receipt = self.w3.eth.waitForTransactionReceipt(txn)
        # print(txn_receipt)

        return Web3.toHex(txn)

    def get_token_price(self, pairing='BUSD'):
        pairing_address = load_data('config/coins.yml')['COINS_CONTRACT'][pairing]
        pairing_address = Web3.toChecksumAddress(pairing_address)

        price = self.router.functions.getAmountsOut(
            int(1 * 10 ** 18),
            [self.token_address, pairing_address]
        ).call()[1]
        return Web3.fromWei(price, 'ether')

    # def get_bnb_balance(self):
    #     balance = self.token_contract.functions.balanceOf(self.address).call()
    #     print(f'balance: {balance}')
    #     return self.token_contract.functions.balanceOf(self.address).call() / (10 ** self.token_contract.functions.decimals().call())
    #
    # def get_token_balance(self):
    #     # balance = self.token_contract.functions.balanceOf(self.address).call()
    #     # print(f'balance: {balance}')
    #     return 1.2

    # def get_bnb_balance(self):
    #     balance = web3.eth.getBalance(self.address)
    #     # print(f"Current balance of {self.token_contract.functions.symbol().call()}: ")
    #     # balance = self.token_contract.functions.balanceOf(self.address)().call()
    #     return Web3.fromWei(balance, 'ether')
    #
    # def get_token_balance(self):
    #     token_contract = self.token_contract.functions.balanceOf(self.address).call()
    #     balance = token_contract.functions.balanceOf(self.address).call()
    #     return self.w3.fromWei(balance, 'ether')
