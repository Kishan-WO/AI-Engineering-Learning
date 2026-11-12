# Where the import name comes from (`ai-service` vs `ai_service`)

Question: how is it decided that the name I type in `import ...` is `ai_service`?

## 1. The short answer
The import name is the **name of the folder** (the package directory) on disk, not the name in `pyproject.toml`.

| Thing | Value in this project | Where it comes from |
|---|---|---|
| **Distribution name** (what `uv add` / `pip install` uses) | `ai-service` | `name = "ai-service"` in `pyproject.toml` |
| **Import name** (what I write in code) | `ai_service` | the folder `src/ai_service/` |

They do not have to match. Dashes are legal in a distribution name but not in a Python identifier, so folders use underscores.

## 2. Compared with npm
| | Node.js | Python |
|---|---|---|
| Name for installing | `package.json` → `"name"` | `pyproject.toml` → `name` |
| Name for importing | the same name: `require("my-cool-package")` | the **folder** name: `import ai_service` |
| Entry file | `"main"` in `package.json` | `__init__.py` in the folder |

In Node the package name decides how it is imported. In Python the folder decides.

## 3. How Python finds the folder
`import ai_service` searches the folders listed in `sys.path`. Two things put my project there:

1. **`src/` layout.** The package sits in `src/ai_service/`, not at the project root. The `src` folder itself is **not** the package.
2. **An editable install.** `uv sync` installs the project into `.venv` and writes a small file:
   ```
   .venv/Lib/site-packages/ai_service.pth
   ```
   Its only content is the path `C:\Projects\ai-eng\ai-service\src`. Python reads every `.pth` file at start-up and adds those paths to `sys.path`, so `import ai_service` finds `src/ai_service/`. Edits to my code take effect at once.

Check it:
```bash
uv run python -c "import ai_service; print(ai_service.__file__)"
# C:\Projects\ai-eng\ai-service\src\ai_service\__init__.py
```

## 4. Why the `src/` layout
| Layout | Problem or benefit |
|---|---|
| Package at the project root | Running Python from the root imports the local folder by accident, even when the install is broken |
| `src/` layout | Code is importable **only** through the install, so tests use the same import path as real users |

## 5. How the build backend knows which folder
`pyproject.toml` has `build-backend = "uv_build"`. For a project named `ai-service` it expects the folder `src/ai_service/` (dashes in the name become underscores). A different folder name needs an extra setting.

## 6. The mistakes that follow
| Mistake | What happens |
|---|---|
| `import ai-service` | `SyntaxError`: a dash is not allowed in a name |
| Renaming the folder but not the imports | `ModuleNotFoundError` |
| Two folders with the same top-level name | The first one on `sys.path` wins |
| Naming my package after a real library (`retry`, `json`, `types`) | Python may import the wrong one |
| Running without the install (`python file.py` with the wrong environment) | `ModuleNotFoundError: No module named 'ai_service'` |

## Quick check
- Where does the import name `ai_service` come from?
- What is the difference between the distribution name and the import name?
- What does the `.pth` file do?
- Why does the `src/` layout stop me from importing code by accident?
