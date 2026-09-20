from dataclasses import dataclass
from pathlib import Path
import os
from statistics import median
import tempfile
from time import perf_counter_ns
from typing import Callable, Iterable, Union


@dataclass(frozen=True)
class ReadObservation:
    bytes_read: int
    elapsed_ns: int

    @property
    def bytes_transferred(self) -> int:
        return self.bytes_read

    @property
    def mebibytes_per_second(self) -> float:
        if self.elapsed_ns <= 0:
            raise ValueError("elapsed time must be positive")
        return (self.bytes_read / (1024 * 1024)) / (self.elapsed_ns / 1_000_000_000)


@dataclass(frozen=True)
class WriteObservation:
    bytes_written: int
    elapsed_ns: int
    synchronized: bool

    @property
    def bytes_transferred(self) -> int:
        return self.bytes_written

    @property
    def mebibytes_per_second(self) -> float:
        if self.elapsed_ns <= 0:
            raise ValueError("elapsed time must be positive")
        return (self.bytes_written / (1024 * 1024)) / (self.elapsed_ns / 1_000_000_000)


@dataclass(frozen=True)
class ThroughputSummary:
    pass_count: int
    total_bytes: int
    total_elapsed_ns: int
    aggregate_mib_per_second: float
    minimum_mib_per_second: float
    median_mib_per_second: float
    maximum_mib_per_second: float
    relative_range: float


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


def measure_sequential_writes(
    directory: Union[str, Path],
    *,
    total_bytes: int,
    chunk_size: int = 1024 * 1024,
    passes: int = 1,
    synchronize: bool = False,
    clock: Callable[[], int] = perf_counter_ns,
) -> list[WriteObservation]:
    if total_bytes < 1 or chunk_size < 1:
        raise ValueError("total_bytes and chunk_size must be positive")
    if passes < 1:
        raise ValueError("passes must be positive")
    target = Path(directory)
    if not target.is_dir():
        raise ValueError("directory must exist")

    chunk = bytes(min(chunk_size, total_bytes))
    observations: list[WriteObservation] = []
    for _ in range(passes):
        with tempfile.NamedTemporaryFile(dir=target, prefix=".io-perf-", buffering=0) as output:
            written = 0
            started = clock()
            while written < total_bytes:
                next_size = min(len(chunk), total_bytes - written)
                output.write(chunk[:next_size])
                written += next_size
            if synchronize:
                os.fsync(output.fileno())
            elapsed = clock() - started
        if elapsed <= 0:
            raise ValueError("clock must advance during a write")
        observations.append(WriteObservation(written, elapsed, synchronize))
    return observations


def summarize_throughput(
    observations: Iterable[Union[ReadObservation, WriteObservation]],
) -> ThroughputSummary:
    items = list(observations)
    if not items:
        raise ValueError("at least one observation is required")
    rates = sorted(item.mebibytes_per_second for item in items)
    total_bytes = sum(item.bytes_transferred for item in items)
    total_elapsed_ns = sum(item.elapsed_ns for item in items)
    middle = median(rates)
    return ThroughputSummary(
        pass_count=len(rates),
        total_bytes=total_bytes,
        total_elapsed_ns=total_elapsed_ns,
        aggregate_mib_per_second=(total_bytes / (1024 * 1024))
        / (total_elapsed_ns / 1_000_000_000),
        minimum_mib_per_second=rates[0],
        median_mib_per_second=middle,
        maximum_mib_per_second=rates[-1],
        relative_range=(rates[-1] - rates[0]) / middle,
    )
