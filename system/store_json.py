import json


def store_order(file, order):
    """
        Save order into local json file
        """
    with open(file, 'w') as f:
        json.dump(order, f, indent=4)


def load_order(file):
    """
    Update Json file
    """
    with open(file, "r+") as f:
        return json.load(f)


def store_last_price(file, price):
    """
        Save last price into local json file
        """
    with open(file, 'w') as f:
        json.dump(price, f, indent=4)


def load_last_price(file):
    """
    Update Json file
    """
    with open(file, "r+") as f:
        return json.load(f)
