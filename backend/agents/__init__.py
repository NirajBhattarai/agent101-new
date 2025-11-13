"""Top-level package for backend agents.

Ensures environment variables from a local `.env` file are loaded as early as
possible for any agent/tool importing from this package. This leverages
python-dotenv which is already included in project dependencies.
"""

from dotenv import load_dotenv

# Load environment variables from a `.env` file located in the current working
# directory or any parent directories. This is a no-op if the file does not
# exist. Keeping this at the package level guarantees tests and runtime pick it
# up without extra boilerplate.
load_dotenv()
