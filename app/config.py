"""Helper functions for making connections to/from services."""
import os


def get_postgres_uri() -> str:
    """Get a postgres connection uri.

    Returns:
        str with connection uri
    """
    host = os.environ.get("DB_HOST", "localhost")
    port = 54321 if host == "localhost" else 5432
    password = os.environ.get("DB_PASSWORD", "abc123")
    user, db_name = "allocation", "allocation"
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"


def get_api_url() -> str:
    """Get a valid url for the flask app.

    Returns:
        str with the flask app.
    """
    host = os.environ.get("API_HOST", "localhost")
    port = 5005 if host == "localhost" else 80
    return f"http://{host}:{port}"
