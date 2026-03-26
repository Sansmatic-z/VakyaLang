# vakvm-rs Dist

This folder keeps the small distributable Rust binaries:

- `vakvm_exec.exe`
- `vakvm_inspect.exe`

The large `target/` directory is only a build cache and can be regenerated with:

```powershell
cargo +stable-x86_64-pc-windows-gnu build --release
```
