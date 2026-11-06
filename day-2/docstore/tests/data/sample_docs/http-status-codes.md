# HTTP Status Codes

Status codes tell the client what happened to its request.

## Success
200 OK, 201 Created and 204 No Content are the most common success codes.

## Client errors
400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found and 429 Too Many Requests. A 429 usually means you should wait and retry.

## Server errors
500 Internal Server Error and 503 Service Unavailable. Many 5xx errors are temporary and safe to retry with backoff.
