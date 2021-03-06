# Copyright (c) Sebastian Scholz
# See LICENSE for details.
#
# This is an example of how to implement oauth2 with this library and twisted.
# It should not be used as is in a real server and is meant as a starting point
# to build your own implementation
import os
import time

from twisted.internet import reactor, endpoints
from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource

from txoauth2 import oauth2, isAuthorized, GrantTypes
from txoauth2.errors import InvalidScopeError
from txoauth2.clients import PasswordClient
from txoauth2.resource import OAuth2
from txoauth2.token import PersistentStorage, TokenResource
from txoauth2.imp import UUIDTokenFactory, ConfigParserClientStorage, DictTokenStorage


class ClockPage(Resource):
    """
    This represents a resource that should be protected via oauth2.

    There are two ways to protect a resource with oauth2:
    1: Use the isAuthorized function and return NOT_DONE_YET if it returns False
    2: use the oauth2 descriptor on one of the render_* functions (or any function, that accepts
       the request as the second argument) and it will call isAuthorized for you.

    Note that we allow requests send over http (allowInsecureRequestDebug=True). This is done
    so one could test this server locally. Do not enable it when running a real server! Don't do it!
    """
    isLeaf = True

    @oauth2('VIEW_CLOCK', allowInsecureRequestDebug=True)
    def render_GET(self, request):
        # This check is not necessary, because this method is already protected by the @oauth
        # decorator. It is included here to show of the two ways of protecting a resource.
        if not isAuthorized(request, 'VIEW_CLOCK', allowInsecureRequestDebug=True):
            return NOT_DONE_YET
        return '<html><body>{time}</body></html>'.format(time=time.ctime()).encode('utf-8')


class PersistentStorageImp(PersistentStorage):
    """
    This implements the PersistentStorage interface. Check out the base class for more detail.

    As with the TokenStorageImp, this implementation does not implement any type of persistence.
    Often persistence is probably not needed here, because the lifetime of the objects stored here
    is commonly very short.
    """
    storage = {}

    def put(self, key, data, expireTime=None):
        self.storage[key] = {
            'data': data,
            'expires': expireTime
        }

    def pop(self, key):
        entry = self.storage.pop(key)
        if entry['expires'] is not None and time.time() > entry['expires']:
            raise KeyError(key)
        return entry['data']


class OAuth2Endpoint(OAuth2):
    """
    This is the Resource that implements the oauth2 endpoint. It will handle the user authorization
    and it hosts the token endpoint.

    Note: This implementation does not verify the user and does not require him to authenticate
    himself. A real implementation should probably do so.
    You are not limited to display a simple web page in onAuthenticate. It is totally valid
    to redirect to a different resource and call grantAccess from there.
    """
    _VALID_SCOPES = ['All', 'VIEW_CLOCK']

    def onAuthenticate(self, request, client, responseType, scope, redirectUri, state, dataKey):
        for scopeItem in scope:
            if scopeItem not in self._VALID_SCOPES:
                return InvalidScopeError(scope, state)
        return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Authorization</title>
</head>
<body>
<form action="/oauth2" method="post">
<p>Allow {client} access to {scope}?</p>
<input type="hidden" name="data_key" value="{dataKey}">
<input type="submit" name="confirm" value="yes">
<input type="submit" name="confirm" value="no">
</form>
</body>
</html>""".format(client=client.id, scope=', '.join(scope), dataKey=dataKey).encode('utf-8')

    def render_POST(self, request):
        """
        This will be called when the user clicks on the "yes" or "no" button in the page
        returned by onAuthenticate.
        """
        dataKey = request.args[b'data_key'][0].decode('utf-8')
        if len(request.args.get(b'confirm', [])) > 0 and request.args[b'confirm'][0] == b'yes':
            return self.grantAccess(request, dataKey)
        else:
            return self.denyAccess(request, dataKey)


def getTestClient():
    """
    :return: A client to use for this example.
    """
    return PasswordClient(
        clientId='test', redirectUris=['https://clientServer.com/return'], secret='test_secret',
        authorizedGrantTypes=[GrantTypes.RefreshToken, GrantTypes.AuthorizationCode])


def setupOAuth2Clients():
    """
    Setup a client storage with a test client.
    :return: The client storage
    """
    clientStoragePath = os.path.join(os.path.dirname(__file__), 'clientStorage')
    clientStorage = ConfigParserClientStorage(clientStoragePath)
    clientStorage.addClient(getTestClient())
    return clientStorage


def setupTestServerResource():
    """
    Setup a test server with a protected clock resource and an oauth2 endpoint.
    :return: The root resource of the test server
    """
    clientStorage = setupOAuth2Clients()
    enabledGrantTypes = [GrantTypes.AuthorizationCode, GrantTypes.RefreshToken]
    tokenResource = TokenResource(
        UUIDTokenFactory(), PersistentStorageImp(), DictTokenStorage(), DictTokenStorage(),
        clientStorage, allowInsecureRequestDebug=True, grantTypes=enabledGrantTypes)
    root = Resource()
    root.putChild(b'clock', ClockPage())
    root.putChild(b'oauth2', OAuth2Endpoint.initFromTokenResource(tokenResource, subPath=b'token',
                                                                  grantTypes=enabledGrantTypes))
    return root


def main():
    """
    Run a test server at localhost:8880.
    """
    factory = Site(setupTestServerResource())
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 8880)
    endpoint.listen(factory)
    # noinspection PyUnresolvedReferences
    reactor.run()


if __name__ == '__main__':
    main()
