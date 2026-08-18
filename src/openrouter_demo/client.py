class PhaseNotImplementedError(NotImplementedError):
    pass


def stream_chat_completion(*args: object, **kwargs: object) -> None:
    raise PhaseNotImplementedError("Live OpenRouter streaming belongs to Phase 2.")
