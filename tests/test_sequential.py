from pathlib import Path
import tempfile
import unittest

from io_performance_kit import (
    ReadObservation,
    measure_sequential_reads,
    measure_sequential_writes,
)


class FakeClock:
    def __init__(self, values: list[int]) -> None:
        self._values = iter(values)

    def __call__(self) -> int:
        return next(self._values)


class SequentialReadTests(unittest.TestCase):
    def test_counts_every_byte_across_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bin"
            path.write_bytes(b"abcdefghij")
            results = measure_sequential_reads(
                path,
                chunk_size=4,
                passes=2,
                clock=FakeClock([0, 10, 20, 40]),
            )
        self.assertEqual([item.bytes_read for item in results], [10, 10])
        self.assertEqual([item.elapsed_ns for item in results], [10, 20])

    def test_computes_binary_throughput(self) -> None:
        result = ReadObservation(1024 * 1024, 1_000_000_000)
        self.assertEqual(result.mebibytes_per_second, 1.0)

    def test_validates_configuration(self) -> None:
        with self.assertRaises(ValueError):
            measure_sequential_reads("missing", chunk_size=0)

    def test_writes_exact_bytes_and_removes_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            results = measure_sequential_writes(
                directory,
                total_bytes=10,
                chunk_size=4,
                passes=2,
                clock=FakeClock([0, 10, 20, 40]),
            )
            self.assertEqual(list(Path(directory).iterdir()), [])
        self.assertEqual([item.bytes_written for item in results], [10, 10])
        self.assertEqual([item.elapsed_ns for item in results], [10, 20])

    def test_validates_write_configuration(self) -> None:
        with self.assertRaises(ValueError):
            measure_sequential_writes("missing", total_bytes=1)


if __name__ == "__main__":
    unittest.main()
