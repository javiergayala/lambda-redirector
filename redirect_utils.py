"""Random utilities used by lambda."""


def str2bool(v):
    """Convert a string to a boolean.

    Arguments:
        v {str} -- string to convert

    Returns:
        {bool} -- True if string is a string representation of True
    """
    return str(v).lower() in ("yes", "true", "t", "1")
