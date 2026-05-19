import logging

# 1. Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 2. Create a handler for writing to a file
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO) # Only log warnings and above to file

# 3. Create a formatter and add it to the handler
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 4. Add the handler to the logger
logger.addHandler(file_handler)
