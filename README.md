# TxOAuth2
This Python module helps to implement an OAuth2 Endpoint in Twisted and provides mechanism to protect resources with OAuth2 authentication.

## Usage

A sample usage can be found in the [example folder](https://github.com/Abestanis/TxOauth2/blob/master/example/main.py).

You will need to create a [TokenResource](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/token.py#L112) and an OAuth2 endpoint by subclassing the [OAuth2 class](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/resource.py#L18)
and insert it somewhere into your server hierarchy (e.g. add both at the same place by using
```python
root.putChild(b"oauth2", OAuth2SubclassInstance.initFromTokenResource(tokenResource, subPath=b"token"))
```
see [the example](https://github.com/Abestanis/TxOauth2/blob/master/example/main.py#L143)).

The OAuth2 subclass will need to overwrite the [onAuthenticate](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/resource.py#L118) method.
This method will be called, when a [User](#terminology) is redirected to your server by a [Client](#terminology) to authorize access to some scope by the client.
Within the method, you should serve or redirect to a page that allows the user to authorize the client.
See [here](https://www.oauth.com/oauth2-servers/scope/user-interface/) to get an idea of how such a page could look like.
If the user approves the authorization, you need to call [grantAccess](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/resource.py#L171)
or [denyAccess](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/resource.py#L154) if the user denies.

Finally, you need to protect your resources either with the [oauth](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/authorization.py#L90)
decorator or by checking the result of [isAuthorized](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/authorization.py#L44)
as demonstrated [here](https://github.com/Abestanis/TxOauth2/blob/master/example/main.py#L36).

This module does not deal with token storage, creation and validation, client storage or persistent storage.
You will need to implement a [TokenFactory](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/token.py#L12),
[TokenStorage](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/token.py#L30),
[PersistentStorage](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/token.py#L83) and
[ClientStorage](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/clients.py#L5).
A few implementations of these interfaces can be found in the [imp package](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/imp.py).

## Installation

Run ```pip install txoauth2``` or download the wheel from [PyPI](https://pypi.python.org/pypi/txoauth2/0.4).

## Terminology

* __User__: A user is the actual owner of a resource and he can grant access to the resource to a client. It is up to you to identify and authenticate a user. You can pass additionalData to ```grantAccess``` that identifies an user. This additional data will be passed to the token generator and storage, which allows for the user information to be encoded into the token.
* __Client__: A client is an other application that wants to access a protected resource that is owned by the user. The client has no rights if they have not been explicitly granted by the user. Clients are represented by [Client objects](https://github.com/Abestanis/TxOauth2/blob/master/txoauth2/clients.py#L21).
* __Token__: There are two types of tokens: Access Tokens and Refresh Tokens. Access Tokens allow access to a protected resource. If they expire, the client can use the Refresh Token to generate a new Access Token. [A token can only contain alphanumeric and the following characters](https://www.oauth.com/oauth2-servers/access-tokens/access-token-response/#token): ```-._~+/```

## Security

The OAuth2 specification requires that the protected resource and the OAuth2 endpoint is served via a secure connection (e.g. https).
To allow insecure connections for local testing, pass ```allowInsecureRequestDebug=True``` where it is accepted.
__Do not do this__ in your real server because everybody will be able to read the tokens and use them to access the protected resources!
