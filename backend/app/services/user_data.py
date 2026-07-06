import logging

logger = logging.getLogger("app.services.user_data")


def lookup_user_data(user_id: str, query: str) -> str | None:
    """Fetch user-specific data from the backend API.

    TODO: wire up the actual backend API endpoint/client once available.
    """
    logger.info("UserData: Attempting lookup for User ID: %s, Query: '%s'", user_id, query)
    logger.warning("UserData: Backend API is not implemented yet. Raising NotImplementedError.")
    raise NotImplementedError("User data backend API is not configured yet")
