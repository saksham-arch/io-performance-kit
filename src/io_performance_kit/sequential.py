from dataclasses import dataclass
from pathlib import Path
from time import perf_counter_ns
from typing import Callable, Union


@dataclass(frozen=True)
class ReadObservation:
    bytes_read: int
    elapsed_ns: int

    @property
    def mebibytes_per_second(self) -> float:
        if self.elapsed_ns <= 0:
            raise ValueError("elapsed time must be positive")
        return (self.bytes_read / (1024 * 1024)) / (self.elapsed_ns / 1_000_000_000)


def measure_sequential_reads(
    path: Union[str, Path],
    *,
    chunk_size: int = 1024 * 1024,
    passes: int = 1,
    clock: Callable[[], int] = perf_counter_ns,
) -> list[ReadObservation]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    if passes < 1:
        raise ValueError("passes must be positive")

    target = Path(path)
    observations: list[ReadObservation] = []
    for _ in range(passes):
        total = 0
        started = clock()
        with target.open("rb", buffering=0) as source:
            while chunk := source.read(chunk_size):
                total += len(chunk)
        elapsed = clock() - started
        if elapsed <= 0:
            raise ValueError("clock must advance during a read")
        observations.append(ReadObservation(total, elapsed))
    return observations
