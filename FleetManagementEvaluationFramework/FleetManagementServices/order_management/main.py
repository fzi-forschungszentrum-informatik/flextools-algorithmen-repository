import os
import log_config.log
import uvicorn

from api.server_api import app
from api.api_config import port, set_service_urls
from config.config_file import LOGGER_NAME

logger = log_config.log.set_logger(LOGGER_NAME)
set_service_urls()

if __name__ == "__main__":
    logger.info('### Starting order management microservice ###')
    uvicorn.run(app, host=os.environ['HOST'], port=port, workers=1)

