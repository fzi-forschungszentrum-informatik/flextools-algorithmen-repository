import json
import logging

import config.config_file

from api.serialization import serialize_json
from data.base_data_file_generator.base_data_file_models import BaseDataFile

logger = logging.getLogger(config.config_file.LOGGER_NAME)

def generate_base_data_file(number_amr: int, file: str):
    base_data_list = []
    for i in range(number_amr):
        base_data_list.append(BaseDataFile(amr_id=str(i+1)))
    data_json = json.dumps(base_data_list, indent=4, default=lambda o: serialize_json(o))
    with open(file, 'w') as f:
        f.write(data_json)
    logger.info(f'Base data file {file} finish generated with {number_amr} AMR!')


if __name__ == "__main__":
    number_amr = 150
    name_file = f"./base_data_file_warehouse_21_35_{number_amr}_amr.json"
    generate_base_data_file(number_amr, name_file)
