use std::env;
use std::process::ExitCode;

use vakvm_rs::abi::AbiEnvelope;

fn main() -> ExitCode {
    let Some(path) = env::args().nth(1) else {
        eprintln!("usage: vakvm_inspect <program.abi.json>");
        return ExitCode::from(2);
    };

    match AbiEnvelope::from_path(&path) {
        Ok(envelope) => {
            let bytecode = envelope.bytecode;
            println!("VakyaLang ABI v{}", envelope.version);
            println!("name: {}", bytecode.name);
            println!("instructions: {}", bytecode.instruction_count());
            println!("constants: {}", bytecode.constants.len());
            println!("locals: {}", bytecode.var_names.len());
            println!("nested_functions: {}", bytecode.total_function_count());
            if let Some(source_path) = bytecode.source_path {
                println!("source_path: {}", source_path);
            }
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("vakvm_inspect: {error}");
            ExitCode::from(1)
        }
    }
}
