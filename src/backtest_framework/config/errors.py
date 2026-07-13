"""Config validation errors.

Per the Step 2 gate in VERIFICATION_SCHEME.md: an invalid config must fail loudly at
factory time, with a message naming the bad key — never silently, and never partway
through a backtest.
"""


class ConfigError(ValueError):
    """A config dict is invalid: missing a required key, has an unknown key, has a value
    of the wrong type, or names an unregistered type. The message always names the
    specific offending key."""
