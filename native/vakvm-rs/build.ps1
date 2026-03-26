$ErrorActionPreference = "Stop"

$cargo = "C:\Users\Admin\.cargo\bin\cargo.exe"

if (-not (Test-Path $cargo)) {
    throw "cargo.exe not found at $cargo"
}

& $cargo +stable-x86_64-pc-windows-gnu test
& $cargo +stable-x86_64-pc-windows-gnu build
