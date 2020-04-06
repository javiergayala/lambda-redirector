"""Random utilities used by lambda."""
import re
import config


def str2bool(v):
    """Convert a string to a boolean.

    Arguments:
        v {str} -- string to convert

    Returns:
        {bool} -- True if string is a string representation of True
    """
    return str(v).lower() in ("yes", "true", "t", "1")


def sanitize_path(path="/"):
    """Sanitize the path provided to the function.

    Keyword Arguments:
        path {str} -- Path that is requested by the user. (default: {"/"})

    Returns:
        {str} -- Sanitized path that was requested
    """
    path = re.sub("/{2,}", "/", path)
    path = path.rstrip("/")
    if config.DEBUG:
        print("===== sanitize_path() DEBUG BEGIN =====")
        print("Sanitized Path: %s" % path)
        print("===== sanitize_path() DEBUG END =====")
    return path


def strip_path(path_to_strip="", uri=""):
    """Strip a particular path from a URI.

    Keyword Arguments:
        path_to_strip {str} -- Path to remove from the URI (default: {""})
        uri {str} -- URI requested (default: {""})

    Returns:
        {str} -- URI with path stripped out
    """
    return re.sub(path_to_strip, "/", uri)
