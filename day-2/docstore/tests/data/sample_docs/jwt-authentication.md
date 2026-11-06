# JWT Authentication

A JSON Web Token (JWT) is a signed token that proves who a user is. It has three parts: header, payload and signature.

After login, the server issues a JWT and the client sends it in the `Authorization: Bearer` header on later requests. The server verifies the signature instead of looking up a session.

Keep tokens short-lived, never store secrets in the payload, and use refresh tokens for long sessions.
