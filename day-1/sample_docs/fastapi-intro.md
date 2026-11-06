# Introduction to FastAPI

FastAPI is a Python web framework for building APIs. It plays a similar role to Express in Node.js.

Routes are declared with decorators such as `@app.get("/items/{item_id}")`. Request bodies are validated automatically with Pydantic models, and FastAPI generates interactive OpenAPI documentation at `/docs`.

FastAPI supports async endpoints, dependency injection with `Depends`, and streaming responses for server-sent events.
