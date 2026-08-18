from openrouter_demo.models import InferenceRun


class RunHistory:
    def __init__(self, max_runs: int = 50) -> None:
        self._max_runs = max_runs
        self._runs: list[InferenceRun] = []

    def append(self, run: InferenceRun) -> None:
        self._runs.append(run)
        if len(self._runs) > self._max_runs:
            self._runs = self._runs[-self._max_runs :]

    def all(self) -> list[InferenceRun]:
        return list(self._runs)