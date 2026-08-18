class PhaseNotImplementedError(NotImplementedError):
    pass


def run_scenario(*args: object, **kwargs: object) -> None:
    raise PhaseNotImplementedError("Routing, fallback, and repeat scenarios belong to later phases.")
