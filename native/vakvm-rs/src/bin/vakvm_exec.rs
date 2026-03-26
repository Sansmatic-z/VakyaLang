use std::env;
use std::process::ExitCode;

use vakvm_rs::abi::AbiEnvelope;
use vakvm_rs::vm::Vm;

fn main() -> ExitCode {
    let Some(path) = env::args().nth(1) else {
        eprintln!("usage: vakvm_exec <program.abi.json>");
        return ExitCode::from(2);
    };

    let envelope = match AbiEnvelope::from_path(&path) {
        Ok(envelope) => envelope,
        Err(error) => {
            eprintln!("vakvm_exec: {error}");
            return ExitCode::from(1);
        }
    };

    match Vm::run_envelope(&envelope) {
        Ok(result) => {
            print!("{}", result.output);
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("vakvm_exec: {error}");
            ExitCode::from(1)
        }
    }
}
