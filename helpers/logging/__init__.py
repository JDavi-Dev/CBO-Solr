import traceback
import logging
from logging.handlers import RotatingFileHandler

# Create a logger with a unique name
logger = logging.getLogger(__name__)

# Configure logger to log messages of INFO, ERROR level and above
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Define a handler to specify where the log messages should be sent
streamHandler = logging.StreamHandler()  # Log messages to console
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Define a RotatingFileHandler to log messages to a rotating set of files
fileHandler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

# Função que aplica tabulação para as informações da exceção
def log_exception(mensagem: str):
    formatted_tb = traceback.format_exc().replace('\n', '\n\t')
    logger.error(f"{mensagem}:\n\t{formatted_tb}")