# Modules, packages, `__init__.py` and `__all__`

Where I met it: `core/__init__.py` with a list called `__all__`.

## 1. Module and package
- A **module** is one `.py` file. `import config` runs `config.py` once and gives me its names.
- A **package** is a folder of modules. A folder with an `__init__.py` file is a regular package.
- `__init__.py` is the package's "front door": it runs the first time the package is imported, and whatever it defines or imports is available as `package.name`.

JavaScript comparison: a folder with an `index.js` that re-exports things (a "barrel file").

```python
# shapes/__init__.py
from shapes.circle import area_of_circle
from shapes.square import area_of_square
__all__ = ["area_of_circle"]
```

## 2. What `__all__` is
`__all__` is a list of strings: the **public names** of the module or package.

It controls exactly one thing: what `from package import *` imports.

```python
from shapes import *
# only area_of_circle arrives, because it is the only name in __all__
```
Real output from my test:
```
star import gives: ['area_of_circle']
shapes.area_of_square still works: 9
```
- `area_of_square` was left out of the star import, but `shapes.area_of_square(3)` or `from shapes import area_of_square` still works. `__all__` hides nothing; it only sets the default for `import *`.
- Without `__all__`, `import *` brings in every name that doesn't start with an underscore.

## 3. Why projects write it anyway
- **A clear list of the public API**: whoever reads `__init__.py` sees what the package offers.
- **Linters treat names in `__all__` as used.** Re-exporting a name with `from x import Y` inside `__init__.py` looks like an unused import to a linter. Listing it in `__all__` says "this is on purpose".
- **Tools and editors** use it for auto-complete and for deciding what is public.

In `ai-service`, `core/__init__.py` imports names from three files and lists them:
```python
from ai_service.core.config import Settings, get_settings
from ai_service.core.logging import setup_logging
from ai_service.core.security import (create_access_token, decode_access_token,
                                      get_password_hash, verify_password)

__all__ = ["Settings", "get_settings", "setup_logging", "get_password_hash",
           "verify_password", "create_access_token", "decode_access_token"]
```
Other code can write `from ai_service.core import get_settings` without knowing which file defines it.

## 4. Imports in a package
| Style | Example | Notes |
|---|---|---|
| Absolute | `from ai_service.core.config import get_settings` | Clear, works from anywhere. Preferred |
| Relative | `from .config import get_settings` | Short, but only works inside the package |

- Circular imports (A imports B, B imports A) fail; fix by moving shared code to a third module.
- `if __name__ == "__main__":` runs code only when a file is started directly, not when it is imported.

## Common mistakes
| Mistake | What happens |
|---|---|
| Thinking `__all__` makes names private | It only affects `import *` |
| A typo in `__all__` | `from package import *` raises `AttributeError` |
| Using `import *` in normal code | Hides where names come from; avoid it |
| Forgetting `__init__.py` | The folder may still import as a namespace package, but tools behave oddly |

## Quick check
- What does `from shapes import *` import when `__all__` exists?
- Does `__all__` stop me from importing a name that is not listed?
- Why do projects list re-exported names in `__all__` even when nobody uses `import *`?
- What is the JavaScript equivalent of `__init__.py`?
