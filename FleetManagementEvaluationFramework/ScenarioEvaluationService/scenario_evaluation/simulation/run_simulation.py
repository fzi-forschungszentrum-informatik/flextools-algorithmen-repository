import logging
import time
import config.config_file

from api.client_api import run_simulation_step
from config.config_file import MAX_EVALUATION_TIME

logger = logging.getLogger(config.config_file.LOGGER_NAME)

def run_simulation():
    error = False
    logger.info('Simulation start running until finish all orders ...')
    finished_percentage = -1
    simulation_res = {'simulationFinish': False, 'percentageFinish': 0}
    start_time_evaluation = time.time()
    while simulation_res['simulationFinish'] is False:
        try:
            simulation_res = run_simulation_step().json()
        except Exception as e:
            logger.info(f'Error in run_simulation_step: {e}')
            error = True
            break
        if finished_percentage != simulation_res['percentageFinish']:
            finished_percentage = simulation_res['percentageFinish']
            logger.info(f'Around {finished_percentage}% of simulated orders are finished executed')
        evaluation_duration = time.time() - start_time_evaluation
        if evaluation_duration > MAX_EVALUATION_TIME:
            logger.info(f'Simulation finish run after exceeding max evaluation time')
            error = True
            break
    if finished_percentage != 100:
        error = True
    logger.info('Simulation finish run')
    return error
