from typing import List

from api.server_api_models import AMRBaseDataInfoResponse


def transform_amr_physical_data_to_api_obj(amr_physical_data) -> List[AMRBaseDataInfoResponse]:
    response = []
    for data in amr_physical_data:
        response.append(AMRBaseDataInfoResponse(maxSpeed=data[0],
                                                accelerationMax=data[1],
                                                decelerationMax=data[2]))

    return response

    