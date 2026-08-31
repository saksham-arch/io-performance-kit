import argparse
from dataclasses import asdict
import json

from .sequential import measure_sequential_reads


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure sequential file reads")
    subparsers = parser.add_subparsers(dest="command", required=True)
    read = subparsers.add_parser("read")
    read.add_argument("path")
    read.add_argument("--chunk-size", type=int, default=1024 * 1024)
    read.add_argument("--passes", type=int, default=1)
    args = parser.parse_args()

    results = measure_sequential_reads(
        args.path, chunk_size=args.chunk_size, passes=args.passes
    )
    payload = [
        {**asdict(result), "mebibytes_per_second": result.mebibytes_per_second}
        for result in results
    ]
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

