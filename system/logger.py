import logging
from datetime import date

today = date.today()

string = today.strftime("%Y_%W")

FORMAT = '%(levelname)s: %(asctime)s | FILE: %(filename)s:%(lineno)d | MESSAGE: %(message)s'
logging.basicConfig(filename=f'logging/{string}.log', level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)
