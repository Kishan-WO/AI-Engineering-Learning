# Environment variables and `.env` with `python-dotenv`

Question: how do I give the Wikipedia contact to the fetcher, and can I use a `.env` file and load it?

## 1. Why not write it in the code
Some values are **settings** (a contact address, an API key, a database password). Putting them in the code means:
- they end up in git and, if pushed, on GitHub,
- changing them means editing code,
- every machine needs the same value.

An **environment variable** is a named value the operating system gives to a program when it starts. The program reads it; the code never contains it. Node comparison: `process.env.NAME` and the `dotenv` package.

## 2. Reading a variable in Python
```python
import os
contact = os.environ.get("WIKI_CONTACT", "")     # "" if it is not set
```
`os.environ` behaves like a dictionary of strings. `.get(name, default)` never raises.

## 3. Setting a variable by hand
| Where | Command | How long it lasts |
|---|---|---|
| PowerShell, this window | `$env:WIKI_CONTACT = "you@example.com"` | until the window closes |
| Git Bash, one command | `WIKI_CONTACT="you@example.com" uv run python fetcher.py` | that command only |
| Windows, permanent | `setx WIKI_CONTACT "you@example.com"` | new windows only |

Check: `echo $env:WIKI_CONTACT` in PowerShell.

## 4. A `.env` file does it for me
A plain text file, one `NAME=value` per line, next to the project:
```
# Local settings. Never committed.
WIKI_CONTACT=you@example.com
```
Install and load it:
```bash
uv add python-dotenv
```
```python
from dotenv import load_dotenv
load_dotenv()                                 # reads .env into os.environ
CONTACT = os.environ.get("WIKI_CONTACT", "")
```
- `load_dotenv()` looks for `.env` starting from the folder of the file that calls it and then upward.
- Rules for the file: no quotes needed, no spaces around `=`, `#` starts a comment.
- **A real environment variable wins** over the `.env` file (by default), so a value set in the terminal overrides the file. I checked this: with `PROJECT_NAME=from-env-var` set in the terminal, the program saw `from-env-var`.

## 5. Keeping secrets out of git
| File | In git? | Purpose |
|---|---|---|
| `.env` | **No**: list it in `.gitignore` | The real values |
| `.env.example` | **Yes** | A template with fake values that shows which variables exist |

`.gitignore`:
```
.env
.env.*
!.env.example
```
Before committing I search the staged files for the secret values (`git grep --cached ...`).

## 6. Make the program fail clearly
If a required value is missing, stop with a clear message instead of failing later with a confusing error:
```python
if not CONTACT:
    raise SystemExit("Fill in WIKI_CONTACT in the .env file.")
```
For many settings, `pydantic-settings` reads the same variables and also validates them (see `pydantic-settings-config.md` in the Day 3 notes).

## 7. A privacy point
A `User-Agent` goes to the website with every request, so it is visible to them. Use a contact I am comfortable sharing (an email or a profile URL), and never type it into code that is committed.

## Common mistakes
| Mistake | What happens |
|---|---|
| Committing `.env` | The secret is public once pushed (history keeps it even after deletion) |
| `WIKI_CONTACT = value` with spaces or quotes in `.env` | The value may include the quotes |
| Editing `.env` and expecting a running program to notice | It is read once at start |
| Calling `load_dotenv()` after reading the variable | The variable is still empty |
| Expecting the file to beat a terminal variable | The terminal variable wins |

## Quick check
- What is an environment variable, and how does Python read one?
- What does `load_dotenv()` do, and which wins, the file or the terminal?
- Which of `.env` and `.env.example` goes into git?
- Why check the secret is not in the staged files before committing?
