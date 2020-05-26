from requests import Session
from sesamutils import sesam_logger
import json


def elwin_workorder(s: Session, url: str, entity: dict):
    logger = sesam_logger("elwin_workorder_handler")

    def do_request(session: Session, method: str, entity: dict):
        resp = None
        if method == 'update':
            resp = session.put(f'{url}/ElWinAvtaler/api/workorders', json=entity)
        elif method == 'get':
            resp = session.get(f'{url}/ElWinAvtaler/api/workorders?externalIds={entity["ExternalId"]}')
        elif method == 'create':
            resp = session.post(f'{url}/ElWinAvtaler/api/workorders', json=entity)
        else:
            logger.critical(f'Critical internal error. "{method}" not valid! Please verify the code. Exiting')
            exit(-1)

        returnval = resp.content.decode('UTF-8')
        logger.debug(f'Method "{method}" for "{entity["_id"]}" gave "{returnval}" & status code: "{resp.status_code}"')
        return returnval


    logger.debug(f'Proccessing entity {entity.get("_id", None)}')
    # If entity has Id then we just update
    if entity.get('Id', None) is not None:
        do_request(s, 'update', entity)
    else:  # Try to find entity based on externalId
        # If response is not JSON then we need to create the entity
        try:
            if "ExternalId" in entity:
                response_entity = json.loads(do_request(s, 'get', entity))
            else:
                response_entity = {}
            if type(response_entity) == list:
                if len(response_entity) == 1:
                    response_entity = response_entity[0]
                else:
                    response_entity = {}
            else:
                response_entity = {}
        except json.JSONDecodeError as e:
            logger.debug(f'Could not GET entity with externalId: "{entity.get("ExternalId", None)}" because of error: "{e}"')
            response_entity = {}

        # If we find the Id then we update, else we create.
        if response_entity.get('Id', None) is not None:
            entity['Id'] = response_entity['Id']
            do_request(s, 'update', entity)
        else:
            if 'Id' in entity:
                del entity['Id']
            do_request(s, 'create', entity)