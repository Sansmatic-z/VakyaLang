use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};
use thiserror::Error;

pub const ABI_FORMAT: &str = "vak_bytecode_abi";
pub const ABI_VERSION: u32 = 1;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct AbiEnvelope {
    pub format: String,
    pub version: u32,
    pub bytecode: BytecodeAbi,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BytecodeAbi {
    pub name: String,
    #[serde(default)]
    pub source_path: Option<String>,
    pub code: Vec<u8>,
    #[serde(default)]
    pub constants: Vec<AbiValue>,
    #[serde(default)]
    pub var_names: Vec<String>,
    #[serde(default)]
    pub param_names: Vec<String>,
    #[serde(default)]
    pub functions: BTreeMap<String, BytecodeAbi>,
    #[serde(default)]
    pub defaults: Vec<AbiValue>,
    #[serde(default)]
    pub varargs_name: Option<String>,
    #[serde(default)]
    pub num_params: u32,
    #[serde(default)]
    pub global_names: Vec<String>,
    #[serde(default)]
    pub type_hints: BTreeMap<String, String>,
    #[serde(default)]
    pub is_async: bool,
    #[serde(default)]
    pub vibhakti_signature: Option<VibhaktiSignatureAbi>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct VibhaktiSignatureAbi {
    #[serde(default)]
    pub params: Vec<VibhaktiParamAbi>,
    #[serde(default)]
    pub return_vibhakti: Option<String>,
    #[serde(default = "default_true")]
    pub strict_mode: bool,
    #[serde(default)]
    pub allow_omission: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct VibhaktiParamAbi {
    pub name: String,
    pub vibhakti: String,
    #[serde(default)]
    pub type_hint: Option<String>,
    #[serde(default)]
    pub default: AbiValue,
    #[serde(default)]
    pub line: u32,
}

fn default_true() -> bool {
    true
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum AbiValue {
    NoDefault,
    Null,
    Bool { value: bool },
    Int { value: i64 },
    Float { value: f64 },
    Str { value: String },
    List { items: Vec<AbiValue> },
    Tuple { items: Vec<AbiValue> },
    Dict { items: BTreeMap<String, AbiValue> },
    CallableRef {
        callable_kind: String,
        name: String,
        #[serde(default)]
        is_async: Option<bool>,
    },
}

impl Default for AbiValue {
    fn default() -> Self {
        Self::Null
    }
}

#[derive(Debug, Error)]
pub enum AbiError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("unsupported ABI format: expected {expected}, got {actual}")]
    UnsupportedFormat { expected: &'static str, actual: String },
    #[error("unsupported ABI version: expected {expected}, got {actual}")]
    UnsupportedVersion { expected: u32, actual: u32 },
}

impl AbiEnvelope {
    pub fn parse_str(json: &str) -> Result<Self, AbiError> {
        let envelope: Self = serde_json::from_str(json)?;
        envelope.validate()?;
        Ok(envelope)
    }

    pub fn from_path(path: impl AsRef<Path>) -> Result<Self, AbiError> {
        let json = fs::read_to_string(path)?;
        Self::parse_str(&json)
    }

    pub fn validate(&self) -> Result<(), AbiError> {
        if self.format != ABI_FORMAT {
            return Err(AbiError::UnsupportedFormat {
                expected: ABI_FORMAT,
                actual: self.format.clone(),
            });
        }
        if self.version != ABI_VERSION {
            return Err(AbiError::UnsupportedVersion {
                expected: ABI_VERSION,
                actual: self.version,
            });
        }
        Ok(())
    }
}

impl BytecodeAbi {
    pub fn instruction_count(&self) -> usize {
        self.code.len()
    }

    pub fn total_function_count(&self) -> usize {
        self.functions
            .values()
            .map(|child| 1 + child.total_function_count())
            .sum()
    }

    pub fn function_names(&self) -> Vec<&str> {
        self.functions.keys().map(String::as_str).collect()
    }
}
