import os.path
# from web3 import Web3
# import json
import time

from service.email_service import send_notification
from service.service import TxnBot, get_bnb_balance, get_token_balance
from system.logger import logger
from system.load_data import load_data
from system.store_json import *


# load coins
coins_to_strategy = load_data('config/coins.yml')['COINS']

# load coins with locked amount (Staking)
locked_amount = load_data('config/coins.yml')['LOCKED']

# loads local configuration
config = load_data('config/config.yml')

# Is on debug mode
debug_mode = load_data('config/config.yml')['DEBUG_MODE']

# Fields of last_transaction.json
price_field = 'price'
available_field = 'available'

# Fields of transactions.json
transaction_field = 'transactions'


def main():
    """
    Run strategy every x number of days.
    """
    while True:
        logger.info("STARTING SCRIPT!")

        # load the order file if it exists
        if os.path.isfile('trades/transactions.json'):
            order = load_order('trades/transactions.json')
        else:
            logger.info("No 'order.json' file found, creating new file")
            order = {}

        # load the last_transaction file if it exists
        if os.path.isfile('trades/last_transaction.json'):
            last_transaction = load_order('trades/last_transaction.json')
        else:
            logger.info("No 'last_transaction.json' file found, creating new file")
            last_transaction = {}

        pairing = config['TRADE_OPTIONS']['PAIRING']
        buy_percent = config['TRADE_OPTIONS']['BUY_PERCENTAGE']  # -5.0
        sell_percent = config['TRADE_OPTIONS']['SELL_PERCENTAGE']  # 10.0
        min_trade = config['TRADE_OPTIONS']['MIN_TRADE']
        send_always_email = config['SEND_ALWAYS_EMAIL']
        send_only_email = config['SEND_ONLY_EMAIL']
        buy_sell_error = False

        email_message = ''

        pairing_market_price = 0.0

        try:
            # Get current market price of coin
            if pairing == 'BNB':
                pairing_market_price = float(TxnBot('WBNB').get_token_price())
            else:
                pairing_market_price = float(TxnBot(pairing).get_token_price())

            time.sleep(2)

        except Exception as e:
            if debug_mode:
                print(f"Error getting {pairing} market price: {e}")

            buy_sell_error = True

            message = f'Something went wrong getting {pairing} market price!\n{e}'
            email_message = f'{email_message} \n{message}'

            logger.warning(f'Can not get {pairing} market price!')
            logger.warning(e)

        if debug_mode:
            print(f'Current {pairing} price: {pairing_market_price}')

        pairing_spot_balance = 0.0

        try:
            # Get spot pairing balance
            if pairing == "BNB" or pairing == "WBNB":
                pairing_spot_balance = float(get_bnb_balance())
            else:
                pairing_spot_balance = float(get_token_balance(token=pairing))

            time.sleep(2)

            if debug_mode:
                print(f'Current {pairing} Spot Balance: {pairing_spot_balance} '
                      f'(${round(pairing_spot_balance * pairing_market_price, 2)})')

        except Exception as e:
            if debug_mode:
                print(f"Error getting {pairing} Spot Balance: {e}")

            buy_sell_error = True

            message = f'Something went wrong getting {pairing} Spot Balance!\n{e}'
            email_message = f'{email_message} \n{message}'

            logger.warning(f'Can not get {pairing} Spot Balance!')
            logger.warning(e)

        # Check if it exists in last_price but not on coins to Buy/Sell
        for key in last_transaction:
            if key not in coins_to_strategy:
                last_transaction[key] = {}

        # Trade each coin
        for coin in coins_to_strategy:
            action = 'HOLD'  # 'BUY', 'HOLD or 'SELL'

            try:
                # Add new coins to traded coins (order.json)
                if coin not in order:
                    order[coin] = {}
                    order[coin][transaction_field] = []

                # If coin do not exist on last_transaction, add it
                if coin not in last_transaction:
                    last_transaction[coin] = {}

                coin_market_price = 0.0

                try:
                    # Get current market price of coin
                    coin_market_price = float(TxnBot(coin).get_token_price())
                    time.sleep(2)

                except Exception as e:
                    buy_sell_error = True

                    message = f'Something went wrong getting {coin} market price!\n{e}'
                    email_message = f'{email_message} \n{message}'

                    logger.warning(f'Can not get {coin} market price!')
                    logger.warning(e)

                if debug_mode:
                    print('')
                    print(f'{coin} current price: {coin_market_price}')

                # Checks if coin really has a last trade price
                # If True, calculates de grow percentage
                if price_field in last_transaction[coin].keys() and last_transaction[coin][price_field] != '':
                    perc_difference = (coin_market_price / float(last_transaction[coin][price_field]) - 1) * 100

                    if debug_mode:
                        print(f'{coin} last price: {last_transaction[coin][price_field]}')
                        print(f'Percentage difference: {"{:.2f}".format(perc_difference)}%\n')
                else:
                    # Only happens when there is no last_transaction (first time running the script)
                    perc_difference = 0.0  # Make it a HOLD

                # Checks if coin really has a last available amount
                if available_field in last_transaction[coin].keys() and last_transaction[coin][available_field] != '':
                    # Get coin balance from account
                    last_coin_balance = last_transaction[coin][available_field]

                else:
                    # Only happens when there is no last_transaction (first time running the script)
                    last_coin_balance = 0.0

                spot_coin_balance = 0.0

                try:
                    # Get coin spot balance
                    if coin == "BNB" or coin == "WBNB":
                        spot_coin_balance = float(get_bnb_balance())
                    else:
                        spot_coin_balance = float(get_token_balance(token=coin))

                    time.sleep(2)

                except Exception as e:
                    buy_sell_error = True

                    message = f'Something went wrong getting {coin} Spot Balance!\n{e}'
                    email_message = f'{email_message} \n{message}'

                    logger.warning(f'Can not get {coin} Spot Balance!')
                    logger.warning(e)

                # Checks if it has locked amount value
                if coin in locked_amount:
                    staked_coin_balance = float(locked_amount[coin])
                else:
                    staked_coin_balance = 0.0

                total_coin_balance = spot_coin_balance + staked_coin_balance

                if debug_mode:
                    print(f'Total {coin} Balance = {total_coin_balance} '
                          f'(${round(total_coin_balance * coin_market_price, 2)})')

                # Protection for redeem before update staked amounts file
                if total_coin_balance > staked_coin_balance * 2 + last_coin_balance:
                    total_coin_balance = spot_coin_balance

                if debug_mode:
                    print(f'Initial {coin} Spot Balance = {spot_coin_balance} '
                          f'(${round(spot_coin_balance * coin_market_price, 2)})')

                # Lost more than 5%
                # Negative grow = BUY
                if perc_difference < buy_percent:
                    action = 'BUY'
                    buy_sell_error = True
                    balance_in_usd = total_coin_balance * float(coin_market_price)
                    buy_qty = balance_in_usd * abs(perc_difference) / 100 * 0.50
                    qty_in_pairing = buy_qty / pairing_market_price
                    rounded_qty_in_pairing = round(qty_in_pairing, 3)

                    if debug_mode:
                        print('')
                        print(f'min_trade: {min_trade}')
                        print(f'rounded_qty: {rounded_qty_in_pairing}')
                        print(f'pairing_spot_balance: {pairing_spot_balance}\n')

                    if rounded_qty_in_pairing >= min_trade:
                        if rounded_qty_in_pairing < pairing_spot_balance:
                            try:
                                # TODO: uncheck this
                                # Create market order
                                # market_order = TxnBot(coin).buy_token(rounded_qty_in_pairing)
                                # time.sleep(2)
                                market_order = 'qwertyuiopasdfghjklzxcvbnm'

                                order[coin][transaction_field].append(market_order)

                                message = f'{action} {rounded_qty_in_pairing} {pairing} of {coin} at ' \
                                          f'{coin_market_price} ({"{:.2f}".format(perc_difference)}) '
                                email_message = f'{email_message} \n{message}'
                                logger.info(message)

                                last_transaction[coin][price_field] = coin_market_price

                                if debug_mode:
                                    print(f'Buy txn: {market_order}')

                            except Exception as e:
                                buy_sell_error = True

                                message = f'Something went wrong creating {action} {coin} market order!\n{e}'
                                email_message = f'{email_message} \n{message}'

                                logger.warning(f'Can not create {action} {coin} market order!')
                                logger.warning(e)

                        else:
                            message = f'Could not {action} {coin} ({rounded_qty_in_pairing}), ' \
                                      f'not enough {pairing} balance!'
                            email_message = f'{email_message} \n{message}'
                            logger.info(message)

                    else:
                        message = f'Could not {action} {coin} ({"{:.2f}".format(perc_difference)}%), ' \
                                        f'quantity under minimum trade'
                        email_message = f'{email_message} \n{message}'
                        logger.info(message)

                        # last_transaction[coin]['price'] = market_price

                # Grow between -5% and 10% = HOLD
                elif buy_percent <= perc_difference <= sell_percent:
                    message = f'{action} {coin} at {coin_market_price} ({"{:.2f}".format(perc_difference)}%)'
                    email_message = f'{email_message} \n{message}'
                    logger.info(message)

                    if price_field not in last_transaction[coin].keys():
                        last_transaction[coin][price_field] = coin_market_price

                # Grow more than 10% = SELL (take some profit)
                elif perc_difference > sell_percent:
                    action = 'SELL'
                    buy_sell_error = True

                    balance_in_usd = total_coin_balance * float(coin_market_price)
                    buy_qty = balance_in_usd * perc_difference / 100 * 0.50
                    qty_in_pairing = buy_qty / pairing_market_price
                    rounded_qty_in_pairing = round(qty_in_pairing, 3)
                    # rounded_qty_in_pairing = round(buy_qty, 1)

                    if debug_mode:
                        print('')
                        print(f'min_trade: {min_trade}')
                        print(f'rounded_qty: {rounded_qty_in_pairing}')
                        print(f'total_coin_balance: {total_coin_balance}\n')
                        print(f'pairing_spot_balance: {pairing_spot_balance}\n')

                    if debug_mode:
                        print(f'total_balance: {total_coin_balance}')

                    # Check if Buy order is above the minimum allow by the exchange
                    # If not = HOLD
                    if rounded_qty_in_pairing >= min_trade:
                        actual_coin_balance_in_usd = spot_coin_balance * coin_market_price
                        sell_qty = total_coin_balance * perc_difference / 100 * 0.50

                        if debug_mode:
                            print(f'rounded_qty {rounded_qty_in_pairing}')
                            print(f'actual_coin_balance_in_usd {actual_coin_balance_in_usd}')
                            print(f'sell_qty {sell_qty}')

                        if spot_coin_balance > sell_qty:
                            try:
                                # TODO: uncheck this
                                # market_order = TxnBot(coin).sell_token(sell_qty)
                                # time.sleep(2)
                                market_order = '123456789'

                                order[coin][transaction_field].append(market_order)

                                message = f'{action} {sell_qty} of {coin} at {coin_market_price} ' \
                                          f'({"{:.2f}".format(perc_difference)}%)'
                                email_message = f'{email_message} \n{message}'
                                logger.info(message)

                                last_transaction[coin][price_field] = coin_market_price

                                if debug_mode:
                                    print(f'Sell txn: {market_order}')

                            except Exception as e:
                                buy_sell_error = True

                                message = f'Something went wrong creating {action} {coin} market order!\n{e}'
                                email_message = f'{email_message} \n{message}'

                                logger.warning(f'Can not create {action} {coin} market order!')
                                logger.warning(e)

                        else:
                            message = f'Not enough {coin} balance to create market order!'
                            email_message = f'{email_message} \n{message}'

                            logger.info(message)

                    else:
                        message = f'Could not {action} {coin} ({"{:.2f}".format(perc_difference)} %), ' \
                                        f'quantity under minimum trade'
                        email_message = f'{email_message} \n{message}'
                        logger.info(message)

                        # last_transaction[coin][price_field] = market_price

                final_coin_spot_balance = 0.0

                try:
                    # Wait some time to transaction approve
                    if action != 'HOLD':
                        time.sleep(30)

                    # Get new coin spot balance after BUY, SELL or HOLD
                    if coin == "BNB" or coin == "WBNB":
                        final_coin_spot_balance = float(get_bnb_balance())
                    else:
                        final_coin_spot_balance = float(get_token_balance(token=coin))

                    time.sleep(2)

                # If something goes wrong getting pairing savings balance
                except Exception as e:
                    buy_sell_error = True

                    message = f'Something went wrong getting {coin} Savings Balance!\n{e}'
                    email_message = f'{email_message} \n{message}'

                    logger.warning(f'Can not get {coin} Savings Balance!')
                    logger.warning(e)

                last_transaction[coin][available_field] = final_coin_spot_balance

                message = f'Actual {coin} Spot Balance = {final_coin_spot_balance} ' \
                          f'(${round(final_coin_spot_balance * float(coin_market_price), 2)})'

                email_message = f'{email_message} \n{message}\n'
                logger.info(message)

                if debug_mode:
                    print(message)

            # If something goes wrong
            except Exception as e:
                if debug_mode:
                    print(f'Error: {e}')

                buy_sell_error = True

                message = f'Something went wrong!\n{e}'
                email_message = f'{email_message} \n{message}'

                logger.warning(f'Order: {action} {coin}')
                logger.warning(e)

            # Everything run well
            else:
                if action != 'HOLD':
                    store_order('trades/transactions.json', order)

                store_last_price('trades/last_transaction.json', last_transaction)
                logger.info(f"Saved price of {coin} ({last_transaction[coin][price_field]})")

            # Before starting new pair
            time.sleep(2)

        spot_pairing_balance = 0.0
        # savings_pairing_balance = 0.0

        # Get pairing balance
        try:
            if pairing == "BNB" or pairing == "WBNB":
                spot_pairing_balance = float(get_bnb_balance())
            else:
                spot_pairing_balance = float(get_token_balance(token=pairing))

            time.sleep(2)

        # If something goes wrong getting pairing spot balance
        except Exception as e:
            buy_sell_error = True

            message = f'Something went wrong getting {pairing} Spot Balance!\n{e}'
            email_message = f'{email_message} \n{message}'

            logger.warning(f'Can not get {pairing} Spot Balance!')
            logger.warning(e)

        message = f'Actual {pairing} Spot Balance = {round(spot_pairing_balance, 5)} ' \
                  f'(${round(spot_pairing_balance * float(pairing_market_price), 2)})'
        email_message = f'{email_message} \n{message}\n'
        logger.info(message)

        if debug_mode:
            print(email_message)

        # Sends an email if enabled.
        if send_always_email or (send_only_email and buy_sell_error):
            send_notification(email_message)

        time.sleep(2)
        logger.info('CLOSING SCRIPT!\n')
        exit()


if __name__ == '__main__':
    main()
