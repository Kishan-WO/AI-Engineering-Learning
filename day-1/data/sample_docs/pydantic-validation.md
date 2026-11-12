# Data Validation with Pydantic

Pydantic validates data using Python type hints. You define a model by subclassing `BaseModel`, and Pydantic checks types when the model is created.

If validation fails, Pydantic raises a `ValidationError` that lists every field that was wrong. Models can be converted to JSON with `model_dump_json()`.

Pydantic is used by FastAPI for request validation and is widely used to validate structured output from LLMs.
