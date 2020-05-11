#rest-receiver
[![Build Status](https://travis-ci.org/sesam-community/oracle-transform.svg?branch=master)](https://travis-ci.org/sesam-community/oracle-transform)


Microservice that handles the sending of entities by using custom (user-created) handlers. 

* Can be used as a sink
* Customization by adding "handlers"
* Listens on port 5001

### Handlers
Handlers are specified in handlers.py.
Current handlers are:
* post
* elwin_workorder

These handlers are accessed by using the URL of a handler. See example curl below.


AUTHORIZATION, if specified, can have following structures

No auth:


    "AUTHORIZATION": None

Basic:

    "AUTHORIZATION": {
      "type": "basic",
      "basic": ["my username", "my password"]
    }

Oauth2:

    "AUTHORIZATION": {
      "type": "oauth2",
      "oauth2": {
        "client_id": "my oauth2 client",
        "client_secret": "my oauth2 secret",
        "token_url": "my oauth2's token url"
      }
    }


Example config:


    [{
      "_id": "rest-receiver",
      "type": "system:microservice",
      "docker":{
        "image": "sesamcommunity/rest-receiver:1.0.0",
        "environment": {
          "handle_me_this_way": {
            "URL": "https://hello.document.reader/api",
           "AUTHORIZATION": {
              "type": "oauth2",
              "oauth2": {
                "client_id": "my oauth2 client",
                "client_secret": "my oauth2 secret",
                "token_url": "my oauth2's token url"
              }
            },
            "HEADERS":{
              "Content-type":"application/json\; charset\=utf-8"
            },
            "HANDLER":"elwin_workorder"
          },          
          "handle_me_another_way": {
            "URL": "https://hello.world/api",
            "AUTHORIZATION":{
              "type": "oauth",
              "basic": ["admin", "root"]
            },
            "HEADERS":{
              "Content-type":"application/json\; charset\=utf-8"
            },
            "HANDLER":"post"
          },
          "LOG_LEVEL": "DEBUG"
        },
        "port": 5001
      },
      "read_timeout": 7200
    },
    {
      "_id": "my-endpoint-pipe",
      "type": "pipe",
      "source": {
        "type": "embedded",
        "entities": [{
            "_id": "foo",
            "value": "bar"
        }]
      },
      "sink": {
        "type": "url",
        "system": "rest-receiver",
        "url": "handle_me_this_way"
      }
    }]

Example curls using handler "handle_me_this_way" which is specified in the env above.

```
curl -s -X POST 'http://localhost:5001/handle_me_this_way' -H "Content-type: application/json" -d '[{ "_id": "jane", "name": "Jane Doe" }]'
```

```
curl -s -XPOST 'http://localhost:5001/handle_me_this_way' -H "Content-type: application/json" -d @sample.json
```

Authorization code borrowed from https://github.com/sesam-community/rest-transform