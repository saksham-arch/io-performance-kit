import argparse
from dataclasses import asdict
import json

from .sequential import measure_sequential_reads, measure_sequential_writes


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure sequential file reads")
    subparsers = parser.add_subparsers(dest="command", required=True)
    read = subparsers.add_parser("read")
    read.add_argument("path")
    read.add_argument("--chunk-size", type=int, default=1024 * 1024)
    read.add_argument("--passes", type=int, default=1)
    write = subparsers.add_parser("write")
    write.add_argument("directory")
    write.add_argument("--total-bytes", type=int, required=True)
    write.add_argument("--chunk-size", type=int, default=1024 * 1024)
    write.add_argument("--passes", type=int, default=1)
    write.add_argument("--synchronize", action="store_true")
    args = parser.parse_args()

    if args.command == "read":
        results = measure_sequential_reads(
            args.path, chunk_size=args.chunk_size, passes=args.passes
        )
    else:
        results = measure_sequential_writes(
            args.directory,
            total_bytes=args.total_bytes,
            chunk_size=args.chunk_size,
            passes=args.passes,
            synchronize=args.synchronize,
        )
    payload = [
        {**asdict(result), "mebibytes_per_second": result.mebibytes_per_second}
        for result in results
    ]
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
