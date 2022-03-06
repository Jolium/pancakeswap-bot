# import requests
# from web3 import Web3
# import time
#
# from system.load_data import load_data
#
# bsc = "https://bsc-dataseed.binance.org/"
# web3 = Web3(Web3.HTTPProvider(bsc))
#
# abi = load_data('config/pancake.yml')['ABI']
# get_token_abi = load_data('config/pancake.yml')['GET_TOKEN_ABI']
#
# panRouterContractAddress = load_data('config/pancake.yml')['ROUTER_CONTRACT_ADDRESS']
# pancakeswapContract = web3.toChecksumAddress(panRouterContractAddress)
#
# sender_address = load_data('auth/auth.yml')['WALLET_ADDRESS']
#
#
# def is_connected():
#     return web3.isConnected()
#
#
# # def get_token_price(token, pairing_token='BUSD'):
# #     """
# #     https://0x.org/docs/api
# #     """
# #     bsc_api = "https://bsc.api.0x.org/swap/v1/"
# #     excluded_sources = "BakerySwap,Belt,DODO,DODO_V2,Ellipsis,Mooniswap,MultiHop,Nerve,Synapse," \
# #                        "SushiSwap,Smoothy,ApeSwap,CafeSwap,CheeseSwap,JulSwap,LiquidityProvider," \
# #                        "WaultSwap,FirebirdOneSwap,JetSwap,ACryptoS,KyberDMM"
# #
# #     buy_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][pairing_token]
# #     sell_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
# #
# #     response = requests.get(f"{bsc_api}quote?"
# #                             f"buyToken={buy_token_address}&"
# #                             f"sellToken={sell_token_address}&"
# #                             f"sellAmount=1000000000000000000&"
# #                             f"excludedSources={excluded_sources}&"
# #                             f"slippagePercentage=0&"
# #                             f"gasPrice=0")
# #
# #     return response.json()['price']
#
#
# def get_token_price2(token, pairing_token='BUSD'):
#     pairing_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][pairing_token]
#     token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
#
#     pairing_token_checksum = web3.toChecksumAddress(pairing_token_address)
#     token_checksum = web3.toChecksumAddress(token_address)
#
#     contract = web3.eth.contract(pancakeswapContract, abi=abi)
#
#     price = contract.functions.getAmountsOut(
#         int(1 * 10 ** 18),
#         [token_checksum, pairing_token_checksum]
#     ).call()[1]
#
#     return web3.fromWei(price, 'ether')
#
#
# # def get_amounts_out_buy(token, amount, slippage):
# #     contract = web3.eth.contract(pancakeswapContract, abi=abi)
# #     buy_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
# #     token_to_buy = web3.toChecksumAddress(buy_token_address)
# #
# #     return contract.functions.getAmountsOut(
# #         int(amount * slippage),
# #         [contract.functions.WETH().call(), token_to_buy]
# #         ).call()
# #
# #
# # def get_amounts_out_sell(token, amount):
# #     contract = web3.eth.contract(pancakeswapContract, abi=abi)
# #     buy_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
# #     token_to_sell = web3.toChecksumAddress(buy_token_address)
# #
# #     return contract.functions.getAmountsOut(
# #         self.token_contract.functions.balanceOf(self.address).call(),
# #         [token_to_sell, contract.functions.WETH().call()]
# #         ).call()
#
#
# def buy_token_amount(token, amount, pairing='WBNB'):
#     pairing_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][pairing]
#     buy_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
#     private_key = load_data('auth/auth.yml')['PRIVATE_KEY']
#
#     contract = web3.eth.contract(pancakeswapContract, abi=abi)
#     pairing_token = web3.toChecksumAddress(pairing_token_address)
#     token_to_buy = web3.toChecksumAddress(buy_token_address)
#
#     nonce = web3.eth.get_transaction_count(sender_address)
#
#     pancakeswap_v2_txn = contract.functions.swapExactETHForTokens(
#         int(1 * 10 ** 18),  # set to 0, or specify minimum amount of tokens you want to receive - consider decimals!!!
#         [pairing_token, token_to_buy],
#         sender_address,
#         (int(time.time()) + 10000)
#     ).buildTransaction({
#         'from': sender_address,
#         'value': web3.toWei(amount, 'ether'),  # This is the Token(BNB) amount you want to Swap from
#         'gas': 250000,
#         'gasPrice': web3.toWei('5', 'gwei'),
#         'nonce': nonce,
#     })
#
#     signed_txn = web3.eth.account.sign_transaction(pancakeswap_v2_txn, private_key=private_key)
#     tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
#
#     return web3.toHex(tx_token)
#
#
# def sell_token_amount(token, amount, pairing='WBNB'):
#     pairing_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][pairing]
#     sell_token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
#     private_key = load_data('auth/auth.yml')['PRIVATE_KEY']
#
#     pairing_token = web3.toChecksumAddress(pairing_token_address)
#     token_to_sell = web3.toChecksumAddress(sell_token_address)
#
#     contract = web3.eth.contract(pancakeswapContract, abi=abi)
#
#     token_amount = web3.toWei(amount, 'ether')
#     nonce = web3.eth.get_transaction_count(sender_address)
#
#     pancakeswap_v2_txn = contract.functions.swapExactTokensForETH(
#         token_amount,
#         0,  # Estimated received tokens (BNB)
#         [token_to_sell, pairing_token],
#         sender_address,
#         (int(time.time()) + 1000000)
#     ).buildTransaction({
#         'from': sender_address,
#         'gas': 250000,
#         'gasPrice': web3.toWei('5', 'gwei'),
#         'nonce': nonce,
#     })
#
#     signed_txn = web3.eth.account.sign_transaction(pancakeswap_v2_txn, private_key=private_key)
#     tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
#
#     return web3.toHex(tx_token)
#
#
# def get_bnb_balance(wallet_address=sender_address):
#     balance = web3.eth.getBalance(wallet_address)
#     return web3.fromWei(balance, 'ether')
#
#
# def get_token_balance(token, wallet_address=sender_address):
#     token_address = load_data('config/coins.yml')['COINS_CONTRACT'][token]
#     token_checksum_address = web3.toChecksumAddress(token_address)
#     token_contract = web3.eth.contract(token_checksum_address, abi=get_token_abi)
#
#     balance = token_contract.functions.balanceOf(wallet_address).call()
#     return web3.fromWei(balance, 'ether')
