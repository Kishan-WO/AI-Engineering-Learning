# REST API Design Guidelines

Good REST APIs use nouns for resources and HTTP methods for actions: `GET /documents`, `POST /documents`, `DELETE /documents/{id}`.

## Guidelines
- Return the right status code: 201 for created, 404 for not found, 422 for invalid input.
- Paginate list endpoints with `limit` and `offset` or a cursor.
- Use a consistent error format across every endpoint.
- Version the API, for example `/v1/documents`.
