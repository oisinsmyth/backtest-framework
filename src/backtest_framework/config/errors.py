"""Config validation errors.

An invalid config raises at factory time, naming the bad key, before any backtest runs.
"""


class ConfigError(ValueError):
    """Raised for an invalid config: a missing or unknown key, a value of the wrong type,
    or an unregistered type. The message names the offending key."""
