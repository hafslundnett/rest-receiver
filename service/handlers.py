from requests import Session
from sesamutils import sesam_logger
import json


def elwin_workorder(s: Session, url: str, entity: dict):
    logger = sesam_logger("elwin_workorder_handler")

    def do_workorders_request(session: Session, method: str, entity: dict):
        resp = None
        #if method == 'update':         # We won't update
        #    resp = session.put(f'{url}/ElWinAvtaler/api/workorders', json=entity)
        if method == 'get':
            resp = session.get(f'{url}/ElWinAvtaler/api/workorders?externalIds={entity["ExternalId"]}')
        elif method == 'create':
            resp = session.post(f'{url}/ElWinAvtaler/api/workorders', json=entity)
        else:
            logger.critical(f'Critical internal error. "{method}" not valid! Please verify the code. Exiting')
            exit(-1)

        returnval = resp.content.decode('UTF-8')
        logger.debug(f'Method "{method}" for "{entity["_id"]}" gave "{returnval}" & status code: "{resp.status_code}"')
        return returnval

    def do_workordermessages_request(session: Session, entity: dict):
        resp = session.post(f'{url}/ElWinAvtaler/api/workordermessages', json=entity)

        returnval = resp.content.decode('UTF-8')
        logger.debug(f'POST to workordermessages gave "{returnval}" & status code: "{resp.status_code}"')
        return returnval

    logger.debug(f'Proccessing entity {entity.get("_id", None)}')
    # If entity has Id then we just update
    message_entity = {
        "WorkorderId": 0, #response_entity.get('Id'),
        "Message": entity.get('Description') # response_entity.get('Description')
    }
    if entity.get('Id', None) is not None:
        logger.warning('We wont update this entity.')
        pass     #We wont update workorders.
#        try:
#            do_workorders_request(s, 'update', entity)
#            message_entity['WorkorderId'] = entity.get('Id', 0)
#        except json.JSONDecodeError as e:
#            logger.debug(f'Could not UPDATE entity with id: "{entity.get("_id", None)}" because of error: "{e}"')

    else:  # Try to find entity based on externalId
        # If response is not JSON then we need to create the entity
        try:
            if "ExternalId" in entity:
                response_entity = json.loads(do_workorders_request(s, 'get', entity))
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
            logger.debug(
                f'Could not GET entity with externalId: "{entity.get("ExternalId", None)}" because of error: "{e}". Entity: {entity}')
            response_entity = {}

        # If we find the Id then we update, else we create.
        if response_entity.get('Id', None) is not None:
            logger.warning('We wont update this entity.')
            pass             # We don't update.
            # entity['Id'] = response_entity['Id']
            # try:
            #     do_workorders_request(s, 'update', entity)
            #     message_entity['WorkorderId'] = response_entity.get('Id', 0)
            # except json.JSONDecodeError as e:
            #     logger.debug(f'Could not UPDATE entity with id: "{entity.get("_id", None)}" because of error: "{e}". Entity: {entity}')
        else:
            if 'Id' in entity:
                del entity['Id']
            try:
                created_entity = json.loads(do_workorders_request(s, 'create', entity))
                message_entity['WorkorderId'] = created_entity.get('Id', 0)

                if message_entity.get('WorkorderId', 0) != 0 or message_entity.get('Description') is not None:
                    do_workordermessages_request(s, message_entity)
                else:
                    logger.error(
                        f'Could not send workordermessage request because the description or workorderid is null: Entity: {message_entity}')
            except json.JSONDecodeError as e:
                logger.debug(f'Could not CREATE entity with id: "{entity.get("_id", None)}" because of error: "{e}". Entity: {entity}')