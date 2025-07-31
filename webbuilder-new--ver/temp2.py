from flask import Flask
import logging

app = Flask(__name__)

# DEBUG, INFO, WARNING, ERROR, CRITICAL
log_level = logging.DEBUG
log_file = 'app.log'
log_file_mode = 'a'
log_format = '%(asctime)s - %(levelname)s - %(message)s'

logging.basicConfig(level=log_level, filename=log_file, filemode=log_file_mode, format=log_format)

# Force a log entry to test
app.logger.info('Starting Flask app')

@app.route('/')
def index():
    # app.logger.info('Index route accessed')
    return "hello world !!"

if __name__ == '__main__':
    app.run(debug=False)
