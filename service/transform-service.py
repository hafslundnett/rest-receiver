from flask import Flask, request, Response
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
import json
import os
import requests
import datetime
from sesamutils import sesam_logger
from sesamutils.flask import serve
import handlers

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 5001))

logger = sesam_logger("rest-transform-service")

do_verify_ssl = os.environ.get("DO_VERIFY_SSL", "false").lower() == "true"

session_factory = None


class BasicUrlSystem:
    def __init__(self, config):
        self._config = config

    def make_session(self):
        session = requests.Session()
        session.auth = tuple(self._config.get("basic")) if self._config.get("basic") else None
        session.headers = self._config["headers"]
        session.verify = do_verify_ssl
        return session


class Oauth2System:
    def __init__(self, config):
        """init Oauth2Client with a json config"""
        self._config = config
        self._get_token()

    def _get_token(self):
        # If no token has been created yet or if the previous token has expired, fetch a new access token
        # before returning the session to the callee
        if not hasattr(self, "_token") or self._token["expires_at"] <= datetime.datetime.now().timestamp():
            oauth2_client = BackendApplicationClient(client_id=self._config["oauth2"]["client_id"])
            session = OAuth2Session(client=oauth2_client)
            logger.debug("Updating token...")
            self._token = session.fetch_token(**self._config["oauth2"])

        logger.debug("expires_at[{}] - now[{}]={} seconds remaining".format(self._token["expires_at"], datetime.datetime.now().timestamp(), self._token["expires_at"] - datetime.datetime.now().timestamp()))
        return self._token

    def make_session(self):
        token = self._get_token()
        client = BackendApplicationClient(client_id=self._config["oauth2"]["client_id"])
        session = OAuth2Session(client=client, token=token)
        session.headers = self._config["headers"]
        session.verify = do_verify_ssl
        return session


def graceful_death(info):
    logger.critical(info)
    return Response(response=info, status=400)


@app.route("/<call_type>", methods=["POST"])
def receiver(call_type):
    def handle_entities(entities):
        handle_as_type = os.environ.get(call_type, None)
        if handle_as_type is None:
            return graceful_death(f'Missing environment var {call_type}')

        type_info = None
        handler = None
        handler_method = None
        try:
            type_info = json.loads(handle_as_type)
            handler = type_info['HANDLER']
            url = type_info['URL']
            authorization = type_info['AUTHORIZATION']
            headers = type_info.get('HEADERS', {})
            if authorization:
                if authorization.get("type", "") == "oauth2":
                    session_factory = Oauth2System({"oauth2": authorization.get("oauth2"), "headers": headers})
                else:
                    session_factory = BasicUrlSystem({"basic": authorization.get("basic"), "headers": headers})
            else:
                session_factory = BasicUrlSystem({"headers": headers})

            handler_method = getattr(handlers, handler)
        except json.JSONDecodeError as e:
            return graceful_death(f'Could not load environment var {call_type} as JSON. Value: {handle_as_type}.\n{e}')
        except KeyError as e:
            return graceful_death(
                f'Env var {type} missing "HANDLER" or "URL" or "AUTHORIZATION". Value: {type_info}.\n{e}')
        except AttributeError as e:
            return graceful_death(f'handlers.py file missing specified handler: "{handler}". \n{e}')

        with session_factory.make_session() as s:
            for entity in entities:
                handler_method(s, url, entity)
        return Response(response={"response": "OK"}, mimetype="application/json", status=200)

    # get entities from request
    request_entities = request.get_json()

    return handle_entities(request_entities)

if __name__ == "__main__":
    serve(app, port=PORT)
