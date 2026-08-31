# io-performance-kit

Transparent, dependency-free tools for inspecting I/O performance. The first
increment measures sequential file reads while keeping the byte count and raw
elapsed time visible.

```bash
python -m io_performance_kit read ./large-test-file.bin --chunk-size 1048576 --passes 3
```

The command emits JSON containing per-pass observations. It does not claim to
evict filesystem caches, so repeated passes may measure cached reads. Use a
representative file, record the storage environment, and interpret throughput
in that context.

Run tests with `python -m unittest discover -s tests`.

