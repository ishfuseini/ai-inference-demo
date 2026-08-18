class PhaseNotImplementedError(NotImplementedError):
    pass


def main() -> None:
    raise PhaseNotImplementedError("Deterministic eval execution belongs to Phase 5.")
