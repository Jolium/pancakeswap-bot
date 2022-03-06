import smtplib
import ssl

from system.load_data import *
from system.logger import logger


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

config = load_data('auth/auth.yml')


def send_notification(message):
    email_address = config['EMAIL_ADDRESS']
    split_email = email_address.split('@')

    subject = f'Notification from your Binance bot'

    if split_email[-1] == 'gmail.com':
        # port = 587
        # smtp_server = "imap.gmail.com"
        #
        # mimemsg = MIMEMultipart()
        # mimemsg['From'] = config['EMAIL_ADDRESS']
        # mimemsg['To'] = config['EMAIL_ADDRESS']
        # mimemsg['Subject'] = subject
        #
        # try:
        #     mimemsg.attach(MIMEText(message, 'plain'))
        #     connection = smtplib.SMTP(host=smtp_server, port=port)
        #     connection.starttls()
        #     connection.login(config['EMAIL_ADDRESS'], config['EMAIL_PASSWORD'])
        #     connection.send_message(mimemsg)
        #     connection.quit()
        #     logger.info('Sent email')
        #
        # except Exception as e:
        #     logger.error(e)

        port = 465
        smtp_server = "imap.gmail.com"

        body = message
        message = 'Subject: {}\n\n{}'.format(subject, body)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(email_address, config['EMAIL_PASSWORD'])
                server.sendmail(email_address, email_address, message)

            logger.info('Sent email')

        except Exception as e:
            logger.error(e)

    elif split_email[-1] == 'hotmail.com':
        port = 587
        smtp_server = "imap-mail.outlook.com"

        mimemsg = MIMEMultipart()
        mimemsg['From'] = config['EMAIL_ADDRESS']
        mimemsg['To'] = config['EMAIL_ADDRESS']
        mimemsg['Subject'] = subject

        try:
            mimemsg.attach(MIMEText(message, 'plain'))
            connection = smtplib.SMTP(host=smtp_server, port=port)
            connection.starttls()
            connection.login(config['EMAIL_ADDRESS'], config['EMAIL_PASSWORD'])
            connection.send_message(mimemsg)
            connection.quit()
            logger.info('Sent email')

        except Exception as e:
            logger.error(e)

    elif split_email[-1] == 'outlook.com':
        port = 587
        smtp_server = "smtp.office365.com"

        mimemsg = MIMEMultipart()
        mimemsg['From'] = config['EMAIL_ADDRESS']
        mimemsg['To'] = config['EMAIL_ADDRESS']
        mimemsg['Subject'] = subject

        try:
            mimemsg.attach(MIMEText(message, 'plain'))
            connection = smtplib.SMTP(host=smtp_server, port=port)
            connection.starttls()
            connection.login(config['EMAIL_ADDRESS'], config['EMAIL_PASSWORD'])
            connection.send_message(mimemsg)
            connection.quit()
            logger.info('Sent email')

        except Exception as e:
            logger.error(e)

    else:
        logger.warning('No email sent!')
