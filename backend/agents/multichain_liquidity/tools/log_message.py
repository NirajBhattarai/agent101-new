"""Log message tool for debugging."""


def log_message(message: str) -> str:
    """
    Log a message for debugging purposes.

    Args:
        message: Message to log

    Returns:
        Confirmation message
    """
    print(f"📝 Log: {message}")
    return f"Logged: {message}"

