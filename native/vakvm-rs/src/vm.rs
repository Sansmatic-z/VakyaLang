use std::cell::RefCell;
use std::collections::BTreeMap;
use std::fmt;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::rc::Rc;
use std::{env, fs};

use thiserror::Error;

use crate::abi::{AbiEnvelope, AbiValue, BytecodeAbi};

const BUILTIN_NAMES: &[&str] = &[
    "पाठ_कर",
    "str",
    "परास",
    "range",
    "दीर्घता",
    "len",
    "प्रकार",
    "type",
    "संख्या",
    "int",
    "दशमलव",
    "float",
    "मुद्रय",
    "print",
    "पठन",
    "लेखन",
    "खोलो",
    "अस्तित्व",
    "मिटाओ",
    "सूची_निर्देशिका",
    "बनाओ_निर्देशिका",
    "परिवेश_प्राप्त",
    "परिवेश_सेट",
    "प्रणाली_कमांड",
    "मंच",
    "कार्य_निर्देशिका",
    "संयोग",
    "विभाजन",
    "छाँटो",
    "उच्च",
    "निम्न",
    "पूर्णांक_कर",
    "क्रमबद्ध",
    "योग",
    "अधिकतम",
    "न्यूनतम",
    "कुंजियाँ",
    "मान",
    "वर्गमूल",
    "परम",
    "_math_cos",
    "_math_sin",
    "_math_tan",
    "_math_sqrt",
    "_math_abs",
    "_math_floor",
    "_math_ceil",
    "_math_round",
    "_math_degrees",
    "_math_radians",
    "जाल_लाओ",
    "जाल_भेजो",
    "जाल_डाउनलोड",
    "जाल_पुट",
    "जाल_हटाओ",
    "समय",
    "निद्रा",
    "धागा_शुरू",
    "सेट_टाइमआउट",
    "सेट_इंटरवल",
    "क्लियर_टाइमआउट",
    "async_sleep",
    "रेगेक्स_खोज",
    "रेगेक्स_बदलो",
    "जेसन_लिखो",
    "जेसन_पढ़ो",
    "परिभाषय",
    "दावा",
    "नियम",
    "मूल्यांकन",
    "सिद्ध_है",
    "आत्म_मूल्य",
    "भाव_पढ़ो",
    "अवस्था_पढ़ो",
    "सभी_भाव",
    "सभी_अवस्था",
    "आत्म_इतिहास",
    "आत्म_है",
    "आत्म_भाव",
    "आत्म_अवस्था",
    "आत्म_मूल",
    "_chitra_canvas",
    "_chitra_fill",
    "_chitra_point",
    "_chitra_line",
    "_chitra_circle",
    "_chitra_rect",
    "_chitra_polygon",
    "_chitra_text",
    "_chitra_save",
    "_chitra_load",
    "_chitra_color",
    "_chitra_colors",
    "_chitra_width",
    "_chitra_height",
    "_chitra_pixel_get",
    "_chitra_pixel_set",
    "_chitra_clear",
    "_chitra_text_centered",
    "_chitra_gradient",
    "_chitra_rotate",
    "_chitra_mandala",
    "_chitra_kaleidoscope",
    "पायथन_आयात",
    "पायथन_चलाओ",
    "पायथन_मूल्यांकन",
    "अक्षर_मान",
    "__match_exception__",
];

#[derive(Debug, Clone)]
pub struct IterState {
    items: Vec<Value>,
    index: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Builtin {
    VakStr,
    Range,
    Len,
    VakType,
    ToInt,
    ToFloat,
    Print,
    Join,
    Split,
    Strip,
    Upper,
    Lower,
    Sorted,
    Sum,
    Max,
    Min,
    DictKeys,
    DictValues,
    Sqrt,
    Abs,
    Round,
    Ord,
    Chr,
    Bool,
    List,
    Dict,
    Callable,
    MatchException,
    Unsupported(String),
}

impl Builtin {
    fn from_name(name: &str) -> Option<Self> {
        let builtin = match name {
            "पाठ_कर" | "str" => Self::VakStr,
            "परास" | "range" => Self::Range,
            "दीर्घता" | "len" => Self::Len,
            "प्रकार" | "type" => Self::VakType,
            "संख्या" | "int" | "पूर्णांक_कर" => Self::ToInt,
            "दशमलव" | "float" => Self::ToFloat,
            "मुद्रय" | "print" => Self::Print,
            "संयोग" => Self::Join,
            "विभाजन" => Self::Split,
            "छाँटो" => Self::Strip,
            "उच्च" => Self::Upper,
            "निम्न" => Self::Lower,
            "क्रमबद्ध" | "sorted" => Self::Sorted,
            "योग" | "sum" => Self::Sum,
            "अधिकतम" | "max" => Self::Max,
            "न्यूनतम" | "min" => Self::Min,
            "कुंजियाँ" => Self::DictKeys,
            "मान" => Self::DictValues,
            "वर्गमूल" | "_math_sqrt" => Self::Sqrt,
            "परम" | "abs" | "_math_abs" => Self::Abs,
            "round" | "_math_round" => Self::Round,
            "अक्षर_मान" | "ord" => Self::Ord,
            "chr" => Self::Chr,
            "bool" => Self::Bool,
            "list" => Self::List,
            "dict" => Self::Dict,
            "callable" => Self::Callable,
            "__match_exception__" => Self::MatchException,
            other if BUILTIN_NAMES.contains(&other) => Self::Unsupported(other.to_string()),
            _ => return None,
        };
        Some(builtin)
    }
}

#[derive(Debug, Clone)]
pub struct VakClass {
    name: String,
    methods: BTreeMap<String, BytecodeAbi>,
    root: Option<Rc<BytecodeAbi>>,
}

#[derive(Debug, Clone)]
pub struct VakInstance {
    klass: Rc<VakClass>,
    attrs: BTreeMap<String, Value>,
}

#[derive(Debug, Clone)]
pub struct VakModule {
    name: String,
    attrs: BTreeMap<String, Value>,
    root: Rc<BytecodeAbi>,
}

#[derive(Debug, Clone)]
pub enum Value {
    Null,
    Bool(bool),
    Int(i64),
    Float(f64),
    Str(String),
    List(Rc<RefCell<Vec<Value>>>),
    Tuple(Vec<Value>),
    Dict(Rc<RefCell<Vec<(Value, Value)>>>),
    FunctionRef {
        name: String,
        is_async: bool,
        root: Option<Rc<BytecodeAbi>>,
    },
    Class(Rc<VakClass>),
    Instance(Rc<RefCell<VakInstance>>),
    Module(Rc<VakModule>),
    BoundMethod {
        object: Box<Value>,
        method_name: String,
    },
    Builtin(Builtin),
    Iterator(Rc<RefCell<IterState>>),
}

impl Value {
    fn from_abi(value: &AbiValue) -> Result<Self, VmError> {
        match value {
            AbiValue::Null => Ok(Self::Null),
            AbiValue::Bool { value } => Ok(Self::Bool(*value)),
            AbiValue::Int { value } => Ok(Self::Int(*value)),
            AbiValue::Float { value } => Ok(Self::Float(*value)),
            AbiValue::Str { value } => Ok(Self::Str(value.clone())),
            AbiValue::List { items } => {
                let mut out = Vec::with_capacity(items.len());
                for item in items {
                    out.push(Self::from_abi(item)?);
                }
                Ok(Self::List(Rc::new(RefCell::new(out))))
            }
            AbiValue::Tuple { items } => {
                let mut out = Vec::with_capacity(items.len());
                for item in items {
                    out.push(Self::from_abi(item)?);
                }
                Ok(Self::Tuple(out))
            }
            AbiValue::Dict { items } => {
                let mut out = Vec::with_capacity(items.len());
                for (key, value) in items {
                    out.push((Self::Str(key.clone()), Self::from_abi(value)?));
                }
                Ok(Self::Dict(Rc::new(RefCell::new(out))))
            }
            AbiValue::CallableRef {
                callable_kind,
                name,
                is_async,
            } => {
                if callable_kind != "function" && callable_kind != "coroutine" {
                    return Err(VmError::UnsupportedValue("callable references"));
                }
                Ok(Self::FunctionRef {
                    name: name.clone(),
                    is_async: is_async.unwrap_or(callable_kind == "coroutine"),
                    root: None,
                })
            }
        }
    }

    fn is_null(&self) -> bool {
        matches!(self, Self::Null)
    }

    fn truthy(&self) -> bool {
        match self {
            Self::Null => false,
            Self::Bool(value) => *value,
            Self::Int(value) => *value != 0,
            Self::Float(value) => *value != 0.0,
            Self::Str(value) => !value.is_empty(),
            Self::List(items) => !items.borrow().is_empty(),
            Self::Tuple(items) => !items.is_empty(),
            Self::Dict(items) => !items.borrow().is_empty(),
            Self::FunctionRef { .. }
            | Self::Class(_)
            | Self::Instance(_)
            | Self::Module(_)
            | Self::BoundMethod { .. }
            | Self::Builtin(_)
            | Self::Iterator(_) => true,
        }
    }

    fn numeric_kind(&self) -> &'static str {
        match self {
            Self::Int(_) => "int",
            Self::Float(_) => "float",
            _ => "non-numeric",
        }
    }

    fn to_f64(&self) -> Result<f64, VmError> {
        match self {
            Self::Int(value) => Ok(*value as f64),
            Self::Float(value) => Ok(*value),
            _ => Err(VmError::TypeMismatch {
                expected: "numeric",
                actual: self.numeric_kind(),
            }),
        }
    }

    fn to_i64(&self) -> Result<i64, VmError> {
        match self {
            Self::Int(value) => Ok(*value),
            Self::Float(value) => Ok(value.trunc() as i64),
            Self::Bool(value) => Ok(if *value { 1 } else { 0 }),
            _ => Err(VmError::TypeMismatch {
                expected: "int-compatible",
                actual: self.type_name(),
            }),
        }
    }

    fn add(self, other: Self) -> Result<Self, VmError> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => Ok(Self::Int(a + b)),
            (Self::Int(a), Self::Float(b)) => Ok(Self::Float(a as f64 + b)),
            (Self::Float(a), Self::Int(b)) => Ok(Self::Float(a + b as f64)),
            (Self::Float(a), Self::Float(b)) => Ok(Self::Float(a + b)),
            (Self::Str(a), Self::Str(b)) => Ok(Self::Str(format!("{a}{b}"))),
            (Self::Str(a), b) => Ok(Self::Str(format!("{a}{}", b.stringify()))),
            (a, Self::Str(b)) => Ok(Self::Str(format!("{}{b}", a.stringify()))),
            (left, right) => Err(VmError::UnsupportedBinary {
                op: "ADD",
                left: left.type_name(),
                right: right.type_name(),
            }),
        }
    }

    fn sub(self, other: Self) -> Result<Self, VmError> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => Ok(Self::Int(a - b)),
            (left, right) => Ok(Self::Float(left.to_f64()? - right.to_f64()?)),
        }
    }

    fn mul(self, other: Self) -> Result<Self, VmError> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => Ok(Self::Int(a * b)),
            (Self::Str(a), Self::Int(b)) if b >= 0 => Ok(Self::Str(a.repeat(b as usize))),
            (Self::Int(a), Self::Str(b)) if a >= 0 => Ok(Self::Str(b.repeat(a as usize))),
            (left, right) => Ok(Self::Float(left.to_f64()? * right.to_f64()?)),
        }
    }

    fn div(self, other: Self) -> Result<Self, VmError> {
        let divisor = other.to_f64()?;
        if divisor == 0.0 {
            return Err(VmError::DivisionByZero);
        }
        Ok(Self::Float(self.to_f64()? / divisor))
    }

    fn idiv(self, other: Self) -> Result<Self, VmError> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => {
                if b == 0 {
                    return Err(VmError::DivisionByZero);
                }
                Ok(Self::Int(a / b))
            }
            (left, right) => {
                let divisor = right.to_f64()?;
                if divisor == 0.0 {
                    return Err(VmError::DivisionByZero);
                }
                Ok(Self::Int((left.to_f64()? / divisor).trunc() as i64))
            }
        }
    }

    fn modulo(self, other: Self) -> Result<Self, VmError> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => {
                if b == 0 {
                    return Err(VmError::DivisionByZero);
                }
                Ok(Self::Int(a % b))
            }
            (left, right) => {
                let divisor = right.to_f64()?;
                if divisor == 0.0 {
                    return Err(VmError::DivisionByZero);
                }
                Ok(Self::Float(left.to_f64()? % divisor))
            }
        }
    }

    fn pow(self, other: Self) -> Result<Self, VmError> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) if b >= 0 => Ok(Self::Int(a.pow(b as u32))),
            (left, right) => Ok(Self::Float(left.to_f64()?.powf(right.to_f64()?))),
        }
    }

    fn neg(self) -> Result<Self, VmError> {
        match self {
            Self::Int(value) => Ok(Self::Int(-value)),
            Self::Float(value) => Ok(Self::Float(-value)),
            other => Err(VmError::UnsupportedUnary {
                op: "NEG",
                actual: other.type_name(),
            }),
        }
    }

    fn cmp_eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Self::Null, Self::Null) => true,
            (Self::Bool(a), Self::Bool(b)) => a == b,
            (Self::Int(a), Self::Int(b)) => a == b,
            (Self::Float(a), Self::Float(b)) => a == b,
            (Self::Int(a), Self::Float(b)) => (*a as f64) == *b,
            (Self::Float(a), Self::Int(b)) => *a == (*b as f64),
            (Self::Str(a), Self::Str(b)) => a == b,
            (Self::Tuple(a), Self::Tuple(b)) => {
                a.len() == b.len() && a.iter().zip(b).all(|(left, right)| left.cmp_eq(right))
            }
            (Self::List(a), Self::List(b)) => {
                let a = a.borrow();
                let b = b.borrow();
                a.len() == b.len() && a.iter().zip(b.iter()).all(|(left, right)| left.cmp_eq(right))
            }
            (Self::Dict(a), Self::Dict(b)) => {
                let a = a.borrow();
                let b = b.borrow();
                a.len() == b.len()
                    && a.iter().all(|(key, value)| {
                        b.iter().any(|(other_key, other_value)| key.cmp_eq(other_key) && value.cmp_eq(other_value))
                    })
            }
            (
                Self::FunctionRef {
                    name: a_name,
                    is_async: a_async,
                    ..
                },
                Self::FunctionRef {
                    name: b_name,
                    is_async: b_async,
                    ..
                },
            ) => a_name == b_name && a_async == b_async,
            (Self::Class(a), Self::Class(b)) => Rc::ptr_eq(a, b),
            (Self::Instance(a), Self::Instance(b)) => Rc::ptr_eq(a, b),
            (Self::Module(a), Self::Module(b)) => Rc::ptr_eq(a, b),
            (
                Self::BoundMethod {
                    object: a_obj,
                    method_name: a_name,
                },
                Self::BoundMethod {
                    object: b_obj,
                    method_name: b_name,
                },
            ) => a_name == b_name && a_obj.cmp_eq(b_obj),
            (Self::Builtin(a), Self::Builtin(b)) => a == b,
            _ => false,
        }
    }

    fn cmp_lt(&self, other: &Self) -> Result<bool, VmError> {
        match (self, other) {
            (Self::Int(a), Self::Int(b)) => Ok(a < b),
            (Self::Float(a), Self::Float(b)) => Ok(a < b),
            (Self::Int(a), Self::Float(b)) => Ok((*a as f64) < *b),
            (Self::Float(a), Self::Int(b)) => Ok(*a < (*b as f64)),
            (Self::Str(a), Self::Str(b)) => Ok(a < b),
            _ => Err(VmError::UnsupportedBinary {
                op: "LT",
                left: self.type_name(),
                right: other.type_name(),
            }),
        }
    }

    fn type_name(&self) -> &'static str {
        match self {
            Self::Null => "null",
            Self::Bool(_) => "bool",
            Self::Int(_) => "int",
            Self::Float(_) => "float",
            Self::Str(_) => "str",
            Self::List(_) => "list",
            Self::Tuple(_) => "tuple",
            Self::Dict(_) => "dict",
            Self::FunctionRef { .. } => "function",
            Self::Class(_) => "class",
            Self::Instance(_) => "instance",
            Self::Module(_) => "module",
            Self::BoundMethod { .. } => "bound_method",
            Self::Builtin(_) => "builtin",
            Self::Iterator(_) => "iterator",
        }
    }

    fn classify(&self) -> String {
        match self {
            Self::Null => "शून्य".to_string(),
            Self::Bool(_) => "बूलियन".to_string(),
            Self::Int(_) | Self::Float(_) => "संख्या".to_string(),
            Self::Str(_) => "तार".to_string(),
            Self::List(_) => "सूची".to_string(),
            Self::Tuple(_) => "टपल".to_string(),
            Self::Dict(_) => "शब्दकोश".to_string(),
            Self::Class(class) => class.name.clone(),
            Self::Instance(instance) => {
                let instance = instance.borrow();
                instance.klass.name.clone()
            }
            Self::Module(_) => "मॉड्यूल".to_string(),
            Self::BoundMethod { .. } => "कार्य".to_string(),
            Self::FunctionRef { .. } | Self::Builtin(_) => "कार्य".to_string(),
            Self::Iterator(_) => "पुनरावर्तक".to_string(),
        }
    }

    fn iter_items(&self) -> Result<Vec<Value>, VmError> {
        match self {
            Self::List(items) => Ok(items.borrow().clone()),
            Self::Tuple(items) => Ok(items.clone()),
            Self::Str(text) => Ok(text.chars().map(|ch| Self::Str(ch.to_string())).collect()),
            Self::Dict(items) => Ok(items.borrow().iter().map(|(key, _)| key.clone()).collect()),
            other => Err(VmError::TypeMismatch {
                expected: "iterable",
                actual: other.type_name(),
            }),
        }
    }

    fn stringify(&self) -> String {
        match self {
            Self::Null => "None".to_string(),
            Self::Bool(true) => "True".to_string(),
            Self::Bool(false) => "False".to_string(),
            Self::Int(value) => value.to_string(),
            Self::Float(value) => {
                let mut text = value.to_string();
                if !text.contains('.') && !text.contains('e') && !text.contains('E') {
                    text.push_str(".0");
                }
                text
            }
            Self::Str(value) => value.clone(),
            Self::List(items) => {
                let inner = items
                    .borrow()
                    .iter()
                    .map(Self::stringify)
                    .collect::<Vec<_>>()
                    .join(", ");
                format!("[{inner}]")
            }
            Self::Tuple(items) => {
                let inner = items.iter().map(Self::stringify).collect::<Vec<_>>().join(", ");
                if items.len() == 1 {
                    format!("({inner},)")
                } else {
                    format!("({inner})")
                }
            }
            Self::Dict(items) => {
                let inner = items
                    .borrow()
                    .iter()
                    .map(|(key, value)| format!("{}: {}", key.stringify(), value.stringify()))
                    .collect::<Vec<_>>()
                    .join(", ");
                format!("{{{inner}}}")
            }
            Self::FunctionRef { name, .. } => format!("<function {name}>"),
            Self::Class(class) => format!("<वर्ग:{}>", class.name),
            Self::Instance(instance) => {
                let instance = instance.borrow();
                format!("<{} वस्तु>", instance.klass.name)
            }
            Self::Module(module) => format!("<module {}>", module.name),
            Self::BoundMethod { method_name, .. } => format!("<bound_method {method_name}>"),
            Self::Builtin(_) => "<builtin>".to_string(),
            Self::Iterator(_) => "<iterator>".to_string(),
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.stringify())
    }
}

#[derive(Debug, Error)]
pub enum VmError {
    #[error("stack underflow")]
    StackUnderflow,
    #[error("invalid local slot {0}")]
    InvalidLocalSlot(usize),
    #[error("invalid constant index {0}")]
    InvalidConstantIndex(usize),
    #[error("unsupported opcode 0x{0:02x} at pc {1}")]
    UnsupportedOpcode(u8, usize),
    #[error("unsupported value kind: {0}")]
    UnsupportedValue(&'static str),
    #[error("unsupported binary operation {op} for {left} and {right}")]
    UnsupportedBinary {
        op: &'static str,
        left: &'static str,
        right: &'static str,
    },
    #[error("unsupported unary operation {op} for {actual}")]
    UnsupportedUnary { op: &'static str, actual: &'static str },
    #[error("type mismatch: expected {expected}, got {actual}")]
    TypeMismatch { expected: &'static str, actual: &'static str },
    #[error("division by zero")]
    DivisionByZero,
    #[error("invalid jump target {0}")]
    InvalidJump(isize),
    #[error("unknown function: {0}")]
    UnknownFunction(String),
    #[error("unsupported async function: {0}")]
    UnsupportedAsyncFunction(String),
    #[error("unexpected keyword argument: {0}")]
    UnexpectedKeywordArgument(String),
    #[error("multiple values for argument: {0}")]
    MultipleValuesForArgument(String),
    #[error("missing required argument: {0}")]
    MissingRequiredArgument(String),
    #[error("too many positional arguments for {0}")]
    TooManyPositionalArguments(String),
    #[error("builtin not supported in native runtime yet: {0}")]
    UnsupportedBuiltin(String),
    #[error("object not callable: {0}")]
    NotCallable(&'static str),
    #[error("keyword argument keys must be strings, got {0}")]
    InvalidKeywordKey(&'static str),
    #[error("invalid index type: {0}")]
    InvalidIndexType(&'static str),
    #[error("index out of range")]
    IndexOutOfRange,
    #[error("attribute '{attribute}' not found on {target}")]
    AttributeNotFound { target: String, attribute: String },
    #[error("module not found: {0}")]
    ModuleNotFound(String),
    #[error("could not locate Vak project root for native import bridge")]
    ProjectRootNotFound,
    #[error("could not locate a usable Python interpreter for native import bridge")]
    PythonNotFound,
    #[error("native import bridge failed: {0}")]
    ImportBridgeFailed(String),
    #[error("unhandled exception: {0}")]
    UnhandledException(String),
}

pub struct ExecutionResult {
    pub output: String,
    pub top: Option<Value>,
}

pub struct Vm {
    output: String,
    globals: BTreeMap<String, Value>,
    module_cache: BTreeMap<String, Rc<VakModule>>,
}

impl Vm {
    pub fn new() -> Self {
        Self {
            output: String::new(),
            globals: BTreeMap::new(),
            module_cache: BTreeMap::new(),
        }
    }

    pub fn run_envelope(envelope: &AbiEnvelope) -> Result<ExecutionResult, VmError> {
        let mut vm = Self::new();
        vm.run(&envelope.bytecode)
    }

    pub fn run(&mut self, bytecode: &BytecodeAbi) -> Result<ExecutionResult, VmError> {
        let top = self.execute_bytecode(
            bytecode,
            bytecode,
            vec![Value::Null; bytecode.var_names.len()],
            true,
        )?;

        Ok(ExecutionResult {
            output: self.output.clone(),
            top,
        })
    }

    fn execute_bytecode(
        &mut self,
        bytecode: &BytecodeAbi,
        root: &BytecodeAbi,
        mut locals: Vec<Value>,
        is_top_level: bool,
    ) -> Result<Option<Value>, VmError> {
        let code = &bytecode.code;
        let mut stack: Vec<Value> = Vec::new();
        let mut pc: usize = 0;
        let mut handlers: Vec<usize> = Vec::new();

        macro_rules! trap {
            ($expr:expr) => {
                match $expr {
                    Ok(value) => value,
                    Err(err) => {
                        if let Some(handler_pc) = handlers.pop() {
                            stack.push(Value::Str(err.to_string()));
                            pc = handler_pc;
                            continue;
                        }
                        return Err(err);
                    }
                }
            };
        }

        while pc < code.len() {
            match code[pc] {
                0x01 => {
                    let idx = read_u16(code, pc + 1)? as usize;
                    let abi_value = bytecode
                        .constants
                        .get(idx)
                        .ok_or(VmError::InvalidConstantIndex(idx))?;
                    stack.push(trap!(Value::from_abi(abi_value)));
                    pc += 3;
                }
                0x02 => {
                    let slot = code[pc + 1] as usize;
                    let name = bytecode
                        .var_names
                        .get(slot)
                        .ok_or(VmError::InvalidLocalSlot(slot))?;
                    let mut value = locals
                        .get(slot)
                        .cloned()
                        .ok_or(VmError::InvalidLocalSlot(slot))?;
                    if value.is_null() {
                        if let Some(global) = self.globals.get(name) {
                            value = global.clone();
                        } else if let Some(builtin) = Builtin::from_name(name) {
                            value = Value::Builtin(builtin);
                        }
                    }
                    stack.push(value);
                    pc += 2;
                }
                0x03 => {
                    let slot = code[pc + 1] as usize;
                    let value = pop(&mut stack)?;
                    let name = bytecode
                        .var_names
                        .get(slot)
                        .cloned()
                        .ok_or(VmError::InvalidLocalSlot(slot))?;
                    if let Some(local) = locals.get_mut(slot) {
                        *local = value.clone();
                    } else {
                        return Err(VmError::InvalidLocalSlot(slot));
                    }
                    if is_top_level || bytecode.global_names.iter().any(|global| global == &name) {
                        self.globals.insert(name, value);
                    }
                    pc += 2;
                }
                0x04 => {
                    trap!(pop(&mut stack));
                    pc += 1;
                }
                0x05 => {
                    let value = stack.last().cloned().ok_or(VmError::StackUnderflow)?;
                    stack.push(value);
                    pc += 1;
                }
                0x06 => {
                    let len = stack.len();
                    if len < 2 {
                        return Err(VmError::StackUnderflow);
                    }
                    stack.swap(len - 1, len - 2);
                    pc += 1;
                }
                0x10 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(trap!(left.add(right)));
                    pc += 1;
                }
                0x11 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(trap!(left.sub(right)));
                    pc += 1;
                }
                0x12 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(trap!(left.mul(right)));
                    pc += 1;
                }
                0x13 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(trap!(left.div(right)));
                    pc += 1;
                }
                0x14 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(trap!(left.modulo(right)));
                    pc += 1;
                }
                0x15 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(trap!(left.pow(right)));
                    pc += 1;
                }
                0x16 => {
                    let value = trap!(pop(&mut stack));
                    stack.push(trap!(value.neg()));
                    pc += 1;
                }
                0x17 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(trap!(left.idiv(right)));
                    pc += 1;
                }
                0x20 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(Value::Bool(left.cmp_eq(&right)));
                    pc += 1;
                }
                0x21 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(Value::Bool(!left.cmp_eq(&right)));
                    pc += 1;
                }
                0x22 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(Value::Bool(trap!(left.cmp_lt(&right))));
                    pc += 1;
                }
                0x23 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(Value::Bool(trap!(right.cmp_lt(&left))));
                    pc += 1;
                }
                0x24 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(Value::Bool(!trap!(right.cmp_lt(&left))));
                    pc += 1;
                }
                0x25 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(Value::Bool(!trap!(left.cmp_lt(&right))));
                    pc += 1;
                }
                0x30 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(Value::Bool(left.truthy() && right.truthy()));
                    pc += 1;
                }
                0x31 => {
                    let right = trap!(pop(&mut stack));
                    let left = trap!(pop(&mut stack));
                    stack.push(Value::Bool(left.truthy() || right.truthy()));
                    pc += 1;
                }
                0x32 => {
                    let value = trap!(pop(&mut stack));
                    stack.push(Value::Bool(!value.truthy()));
                    pc += 1;
                }
                0x40 => {
                    let offset = read_i16(code, pc + 1)? as isize;
                    pc = jump_target(pc, 3, offset, code.len())?;
                }
                0x41 => {
                    let offset = read_i16(code, pc + 1)? as isize;
                    let cond = trap!(pop(&mut stack));
                    if cond.truthy() {
                        pc = jump_target(pc, 3, offset, code.len())?;
                    } else {
                        pc += 3;
                    }
                }
                0x42 => {
                    let offset = read_i16(code, pc + 1)? as isize;
                    let cond = trap!(pop(&mut stack));
                    if !cond.truthy() {
                        pc = jump_target(pc, 3, offset, code.len())?;
                    } else {
                        pc += 3;
                    }
                }
                0x50 | 0x56 => {
                    let argc = code[pc + 1] as usize;
                    let kwargs = if code[pc] == 0x56 {
                        trap!(pop_kwargs(&mut stack))
                    } else {
                        BTreeMap::new()
                    };
                    let args = trap!(pop_n(&mut stack, argc));
                    let callee = trap!(pop(&mut stack));
                    let result = trap!(self.call_value(callee, args, kwargs, root));
                    stack.push(result);
                    pc += 2;
                }
                0x51 => return Ok(Some(trap!(pop(&mut stack)))),
                0x52 => return Ok(Some(Value::Null)),
                0x53 => {
                    let class_name = trap!(pop(&mut stack));
                    let parent = trap!(pop(&mut stack));
                    let class_name = class_name.stringify();
                    let class_bc = bytecode
                        .functions
                        .get(&class_name)
                        .ok_or_else(|| VmError::UnknownFunction(class_name.clone()))?;

                    let mut methods = match parent {
                        Value::Class(parent_class) => parent_class.methods.clone(),
                        Value::Null => BTreeMap::new(),
                        other => {
                            return Err(VmError::TypeMismatch {
                                expected: "class or null",
                                actual: other.type_name(),
                            })
                        }
                    };
                    for (method_name, method_bc) in &class_bc.functions {
                        methods.insert(method_name.clone(), method_bc.clone());
                    }

                    stack.push(Value::Class(Rc::new(VakClass {
                        name: class_name,
                        methods,
                        root: Some(Rc::new(root.clone())),
                    })));
                    pc += 1;
                }
                0x54 | 0x57 => {
                    let argc = code[pc + 1] as usize;
                    let kwargs = if code[pc] == 0x57 {
                        trap!(pop_kwargs(&mut stack))
                    } else {
                        BTreeMap::new()
                    };
                    let args = trap!(pop_n(&mut stack, argc));
                    let method_name = trap!(pop(&mut stack)).stringify();
                    let object = trap!(pop(&mut stack));
                    let result = trap!(self.call_method_named(object, &method_name, args, kwargs, root));
                    stack.push(result);
                    pc += 2;
                }
                0x55 => {
                    let count = code[pc + 1] as usize;
                    let values = trap!(pop_n(&mut stack, count));
                    let joined = values
                        .iter()
                        .map(Value::stringify)
                        .collect::<Vec<_>>()
                        .join("");
                    stack.push(Value::Str(joined));
                    pc += 2;
                }
                0x60 => {
                    let count = code[pc + 1] as usize;
                    let items = trap!(pop_n(&mut stack, count));
                    stack.push(Value::List(Rc::new(RefCell::new(items))));
                    pc += 2;
                }
                0x61 => {
                    let count = code[pc + 1] as usize;
                    let mut pairs = Vec::with_capacity(count);
                    for _ in 0..count {
                        let key = trap!(pop(&mut stack));
                        let value = trap!(pop(&mut stack));
                        pairs.push((key, value));
                    }
                    pairs.reverse();
                    stack.push(Value::Dict(Rc::new(RefCell::new(pairs))));
                    pc += 2;
                }
                0x62 => {
                    let index = trap!(pop(&mut stack));
                    let object = trap!(pop(&mut stack));
                    stack.push(trap!(index_get(&object, &index)));
                    pc += 1;
                }
                0x63 => {
                    let value = trap!(pop(&mut stack));
                    let index = trap!(pop(&mut stack));
                    let object = trap!(pop(&mut stack));
                    trap!(index_set(&object, &index, value));
                    pc += 1;
                }
                0x64 => {
                    let attr_index = read_u16(code, pc + 1)? as usize;
                    let attr_name = bytecode
                        .constants
                        .get(attr_index)
                        .ok_or(VmError::InvalidConstantIndex(attr_index))?
                        .clone();
                    let attr_name = trap!(Value::from_abi(&attr_name)).stringify();
                    let object = trap!(pop(&mut stack));
                    let value = trap!(get_attr(object, &attr_name));
                    stack.push(value);
                    pc += 3;
                }
                0x65 => {
                    let attr_index = read_u16(code, pc + 1)? as usize;
                    let attr_name = bytecode
                        .constants
                        .get(attr_index)
                        .ok_or(VmError::InvalidConstantIndex(attr_index))?
                        .clone();
                    let attr_name = trap!(Value::from_abi(&attr_name)).stringify();
                    let value = trap!(pop(&mut stack));
                    let object = trap!(pop(&mut stack));
                    trap!(set_attr(&object, &attr_name, value));
                    pc += 3;
                }
                0x66 => {
                    let iterable = trap!(pop(&mut stack));
                    let items = trap!(iterable.iter_items());
                    stack.push(Value::Iterator(Rc::new(RefCell::new(IterState {
                        items,
                        index: 0,
                    }))));
                    pc += 1;
                }
                0x67 => {
                    let offset = read_i16(code, pc + 1)? as isize;
                    match stack.last().cloned() {
                        Some(Value::Iterator(iter_ref)) => {
                            let mut iter = iter_ref.borrow_mut();
                            if iter.index < iter.items.len() {
                                let item = iter.items[iter.index].clone();
                                iter.index += 1;
                                drop(iter);
                                stack.push(item);
                                pc += 3;
                            } else {
                                drop(iter);
                                trap!(pop(&mut stack));
                                pc = jump_target(pc, 3, offset, code.len())?;
                            }
                        }
                        Some(other) => {
                            return Err(VmError::TypeMismatch {
                                expected: "iterator",
                                actual: other.type_name(),
                            })
                        }
                        None => return Err(VmError::StackUnderflow),
                    }
                }
                0x68 => {
                    let offset = read_i16(code, pc + 1)? as isize;
                    handlers.push(jump_target(pc, 3, offset, code.len())?);
                    pc += 3;
                }
                0x69 => {
                    handlers.pop();
                    pc += 1;
                }
                0x6a => {
                    let value = trap!(pop(&mut stack));
                    if let Some(handler_pc) = handlers.pop() {
                        stack.push(value);
                        pc = handler_pc;
                    } else {
                        return Err(VmError::UnhandledException(value.stringify()));
                    }
                }
                0x6b => {
                    let idx = read_u16(code, pc + 1)? as usize;
                    let module_name = bytecode
                        .constants
                        .get(idx)
                        .ok_or(VmError::InvalidConstantIndex(idx))?
                        .clone();
                    let module_name = trap!(Value::from_abi(&module_name)).stringify();
                    let module = trap!(self.import_module(&module_name, bytecode));
                    stack.push(Value::Module(module));
                    pc += 3;
                }
                0x6d => {
                    let value = trap!(pop(&mut stack));
                    let list = stack
                        .get(stack.len().saturating_sub(2))
                        .cloned()
                        .ok_or(VmError::StackUnderflow)?;
                    match list {
                        Value::List(items) => items.borrow_mut().push(value),
                        other => {
                            return Err(VmError::TypeMismatch {
                                expected: "list",
                                actual: other.type_name(),
                            })
                        }
                    }
                    pc += 1;
                }
                0x6e => {
                    let count = code[pc + 1] as usize;
                    let sequence = trap!(pop(&mut stack));
                    let items = trap!(sequence.iter_items());
                    if items.len() != count {
                        return Err(VmError::TypeMismatch {
                            expected: "sequence with matching arity",
                            actual: sequence.type_name(),
                        });
                    }
                    for item in items.into_iter().rev() {
                        stack.push(item);
                    }
                    pc += 2;
                }
                0x70 => {
                    let value = trap!(pop(&mut stack));
                    self.output.push_str(&value.stringify());
                    pc += 1;
                }
                0x71 => {
                    let idx = read_u16(code, pc + 1)? as usize;
                    let argc = *code
                        .get(pc + 3)
                        .ok_or(VmError::InvalidJump((pc + 3) as isize))? as usize;
                    let args = pop_n(&mut stack, argc)?;
                    let builtin_name = BUILTIN_NAMES
                        .get(idx)
                        .ok_or_else(|| VmError::UnsupportedBuiltin(format!("index {idx}")))?;
                    let builtin = Builtin::from_name(builtin_name)
                        .unwrap_or_else(|| Builtin::Unsupported((*builtin_name).to_string()));
                    let result = trap!(self.call_builtin(builtin, args, BTreeMap::new()));
                    stack.push(result);
                    pc += 4;
                }
                0x72 => {
                    let count = code[pc + 1] as usize;
                    let items = trap!(pop_n(&mut stack, count));
                    stack.push(Value::Tuple(items));
                    pc += 2;
                }
                0x82 => {
                    let object = trap!(pop(&mut stack));
                    let cleanup_result = match &object {
                        Value::Instance(instance) => {
                            let class = instance.borrow().klass.clone();
                            if class.methods.contains_key("__exit__") {
                                self.call_method_named(
                                    object.clone(),
                                    "__exit__",
                                    vec![Value::Null, Value::Null, Value::Null],
                                    BTreeMap::new(),
                                    root,
                                )
                            } else if class.methods.contains_key("बंद_कर") {
                                self.call_method_named(object.clone(), "बंद_कर", Vec::new(), BTreeMap::new(), root)
                            } else {
                                Ok(Value::Null)
                            }
                        }
                        _ => Ok(Value::Null),
                    };
                    let _ = trap!(cleanup_result);
                    pc += 1;
                }
                0xff => break,
                opcode => return Err(VmError::UnsupportedOpcode(opcode, pc)),
            }
        }

        Ok(stack.last().cloned())
    }

    fn call_value(
        &mut self,
        callee: Value,
        args: Vec<Value>,
        kwargs: BTreeMap<String, Value>,
        root: &BytecodeAbi,
    ) -> Result<Value, VmError> {
        match callee {
            Value::FunctionRef {
                name,
                is_async,
                root: function_root,
            } => {
                if is_async {
                    return Err(VmError::UnsupportedAsyncFunction(name));
                }
                let function_root_ref = function_root.as_deref().unwrap_or(root);
                let function = find_function(function_root_ref, &name)
                    .ok_or_else(|| VmError::UnknownFunction(name.clone()))?;
                let locals = self.bind_call_arguments_with_receiver(function, args, kwargs, None)?;
                Ok(self
                    .execute_bytecode(function, function_root_ref, locals, false)?
                    .unwrap_or(Value::Null))
            }
            Value::Class(class) => self.instantiate_class(class, args, kwargs, root),
            Value::BoundMethod { object, method_name } => {
                self.call_method_named(*object, &method_name, args, kwargs, root)
            }
            Value::Builtin(builtin) => self.call_builtin(builtin, args, kwargs),
            other => Err(VmError::NotCallable(other.type_name())),
        }
    }

    fn bind_call_arguments_with_receiver(
        &mut self,
        bytecode: &BytecodeAbi,
        args: Vec<Value>,
        kwargs: BTreeMap<String, Value>,
        receiver: Option<Value>,
    ) -> Result<Vec<Value>, VmError> {
        let num_params = bytecode.num_params as usize;
        let mut locals = vec![Value::Null; bytecode.var_names.len()];
        let self_offset = usize::from(receiver.is_some());
        if let Some(receiver_value) = receiver {
            if !locals.is_empty() {
                locals[0] = receiver_value;
            }
        }

        let param_names = if bytecode.param_names.len() >= num_params {
            bytecode.param_names[self_offset..num_params].to_vec()
        } else {
            bytecode
                .var_names
                .iter()
                .skip(self_offset)
                .take(num_params.saturating_sub(self_offset))
                .cloned()
                .collect()
        };

        let user_param_count = num_params.saturating_sub(self_offset);
        let mut assigned = vec![false; user_param_count];
        let positional_to_assign = args.len().min(user_param_count);
        for (index, arg) in args.iter().take(positional_to_assign).cloned().enumerate() {
            locals[self_offset + index] = arg;
            assigned[index] = true;
        }

        if args.len() > user_param_count && bytecode.varargs_name.is_none() {
            return Err(VmError::TooManyPositionalArguments(bytecode.name.clone()));
        }

        for (name, value) in kwargs {
            let Some(param_index) = param_names.iter().position(|param| param == &name) else {
                return Err(VmError::UnexpectedKeywordArgument(name));
            };
            if assigned[param_index] {
                return Err(VmError::MultipleValuesForArgument(name));
            }
            locals[self_offset + param_index] = value;
            assigned[param_index] = true;
        }

        let mut defaults = bytecode
            .defaults
            .iter()
            .map(Value::from_abi)
            .collect::<Result<Vec<_>, _>>()?;
        if defaults.len() < num_params {
            let mut padded = vec![Value::Null; num_params - defaults.len()];
            padded.extend(defaults);
            defaults = padded;
        } else if defaults.len() > num_params {
            defaults.truncate(num_params);
        }

        for index in 0..user_param_count {
            if assigned[index] {
                continue;
            }
            let local_index = self_offset + index;
            let default_value = defaults.get(local_index).cloned().unwrap_or(Value::Null);
            if !default_value.is_null() {
                locals[local_index] = default_value;
            } else {
                let name = param_names
                    .get(index)
                    .cloned()
                    .unwrap_or_else(|| format!("arg{index}"));
                return Err(VmError::MissingRequiredArgument(name));
            }
        }

        if bytecode.varargs_name.is_some() {
            let extras = args.into_iter().skip(user_param_count).collect::<Vec<_>>();
            if num_params < locals.len() {
                locals[num_params] = Value::List(Rc::new(RefCell::new(extras)));
            }
        }

        Ok(locals)
    }

    fn instantiate_class(
        &mut self,
        class: Rc<VakClass>,
        args: Vec<Value>,
        kwargs: BTreeMap<String, Value>,
        fallback_root: &BytecodeAbi,
    ) -> Result<Value, VmError> {
        let instance = Rc::new(RefCell::new(VakInstance {
            klass: class.clone(),
            attrs: BTreeMap::new(),
        }));
        let instance_value = Value::Instance(instance.clone());

        if let Some(constructor_name) = self.constructor_name(&class) {
            let constructor = class
                .methods
                .get(constructor_name)
                .ok_or_else(|| VmError::UnknownFunction(constructor_name.to_string()))?;
            let constructor_root = class.root.as_deref().unwrap_or(fallback_root);
            let locals = self.bind_call_arguments_with_receiver(
                constructor,
                args,
                kwargs,
                Some(instance_value.clone()),
            )?;
            let _ = self.execute_bytecode(constructor, constructor_root, locals, false)?;
        } else if !args.is_empty() || !kwargs.is_empty() {
            return Err(VmError::TooManyPositionalArguments(class.name.clone()));
        }

        Ok(instance_value)
    }

    fn constructor_name<'a>(&self, class: &'a VakClass) -> Option<&'a str> {
        if class.methods.contains_key("प्रारम्भ") {
            Some("प्रारम्भ")
        } else if class.methods.contains_key("__init__") {
            Some("__init__")
        } else {
            None
        }
    }

    fn call_method_named(
        &mut self,
        object: Value,
        method_name: &str,
        args: Vec<Value>,
        kwargs: BTreeMap<String, Value>,
        fallback_root: &BytecodeAbi,
    ) -> Result<Value, VmError> {
        match object {
            Value::Instance(instance) => {
                let class = instance.borrow().klass.clone();
                if let Some(method) = class.methods.get(method_name) {
                    let method_root = class.root.as_deref().unwrap_or(fallback_root);
                    let locals = self.bind_call_arguments_with_receiver(
                        method,
                        args,
                        kwargs,
                        Some(Value::Instance(instance.clone())),
                    )?;
                    Ok(self
                        .execute_bytecode(method, method_root, locals, false)?
                        .unwrap_or(Value::Null))
                } else if method_name == "__enter__" {
                    Ok(Value::Instance(instance))
                } else {
                    Err(VmError::AttributeNotFound {
                        target: class.name.clone(),
                        attribute: method_name.to_string(),
                    })
                }
            }
            Value::Module(module) => {
                let value = module.attrs.get(method_name).cloned().ok_or_else(|| VmError::AttributeNotFound {
                    target: format!("module {}", module.name),
                    attribute: method_name.to_string(),
                })?;
                self.call_value(value, args, kwargs, module.root.as_ref())
            }
            Value::List(items) => self.call_list_method(items, method_name, args, kwargs),
            Value::Dict(items) => self.call_dict_method(items, method_name, args, kwargs),
            Value::Str(text) => self.call_string_method(text, method_name, args, kwargs),
            other => Err(VmError::AttributeNotFound {
                target: other.type_name().to_string(),
                attribute: method_name.to_string(),
            }),
        }
    }

    fn call_list_method(
        &mut self,
        items: Rc<RefCell<Vec<Value>>>,
        method_name: &str,
        args: Vec<Value>,
        kwargs: BTreeMap<String, Value>,
    ) -> Result<Value, VmError> {
        reject_kwargs(method_name, &kwargs)?;
        match method_name {
            "append" | "जोड़ो" => {
                if let Some(value) = args.first() {
                    items.borrow_mut().push(value.clone());
                }
                Ok(Value::Null)
            }
            "pop" | "निकालो" | "हटाओ" => Ok(items.borrow_mut().pop().unwrap_or(Value::Null)),
            "clear" | "स्वच्छ" => {
                items.borrow_mut().clear();
                Ok(Value::Null)
            }
            "extend" | "विस्तार" => {
                if let Some(value) = args.first() {
                    items.borrow_mut().extend(value.iter_items()?);
                }
                Ok(Value::Null)
            }
            "count" | "गणना" => {
                let needle = args.first().cloned().unwrap_or(Value::Null);
                let count = items.borrow().iter().filter(|item| item.cmp_eq(&needle)).count();
                Ok(Value::Int(count as i64))
            }
            "index" | "अनुक्रमणिका" => {
                let needle = args.first().cloned().unwrap_or(Value::Null);
                let position = items
                    .borrow()
                    .iter()
                    .position(|item| item.cmp_eq(&needle))
                    .ok_or(VmError::IndexOutOfRange)?;
                Ok(Value::Int(position as i64))
            }
            "reverse" | "विपरीत" => {
                items.borrow_mut().reverse();
                Ok(Value::Null)
            }
            "sort" | "क्रमबद्ध" => {
                items.borrow_mut().sort_by_key(Value::stringify);
                Ok(Value::Null)
            }
            _ => Err(VmError::AttributeNotFound {
                target: "list".to_string(),
                attribute: method_name.to_string(),
            }),
        }
    }

    fn call_dict_method(
        &mut self,
        items: Rc<RefCell<Vec<(Value, Value)>>>,
        method_name: &str,
        args: Vec<Value>,
        kwargs: BTreeMap<String, Value>,
    ) -> Result<Value, VmError> {
        reject_kwargs(method_name, &kwargs)?;
        match method_name {
            "keys" | "कुंजियाँ" => Ok(Value::List(Rc::new(RefCell::new(
                items.borrow().iter().map(|(key, _)| key.clone()).collect(),
            )))),
            "values" | "मान" => Ok(Value::List(Rc::new(RefCell::new(
                items.borrow().iter().map(|(_, value)| value.clone()).collect(),
            )))),
            "get" => {
                let key = args.first().cloned().unwrap_or(Value::Null);
                let default = args.get(1).cloned().unwrap_or(Value::Null);
                for (existing_key, existing_value) in items.borrow().iter() {
                    if existing_key.cmp_eq(&key) {
                        return Ok(existing_value.clone());
                    }
                }
                Ok(default)
            }
            _ => Err(VmError::AttributeNotFound {
                target: "dict".to_string(),
                attribute: method_name.to_string(),
            }),
        }
    }

    fn call_string_method(
        &mut self,
        text: String,
        method_name: &str,
        args: Vec<Value>,
        kwargs: BTreeMap<String, Value>,
    ) -> Result<Value, VmError> {
        reject_kwargs(method_name, &kwargs)?;
        match method_name {
            "upper" | "उच्च" => Ok(Value::Str(text.to_uppercase())),
            "lower" | "निम्न" => Ok(Value::Str(text.to_lowercase())),
            "strip" | "छाँटो" => Ok(Value::Str(text.trim().to_string())),
            "split" | "विभाजन" => {
                let separator = args
                    .first()
                    .cloned()
                    .unwrap_or_else(|| Value::Str(" ".to_string()))
                    .stringify();
                let pieces = if separator.is_empty() {
                    text.chars().map(|ch| Value::Str(ch.to_string())).collect()
                } else {
                    text.split(&separator)
                        .map(|part| Value::Str(part.to_string()))
                        .collect()
                };
                Ok(Value::List(Rc::new(RefCell::new(pieces))))
            }
            _ => Err(VmError::AttributeNotFound {
                target: "str".to_string(),
                attribute: method_name.to_string(),
            }),
        }
    }

    fn import_module(
        &mut self,
        module_name: &str,
        current_bytecode: &BytecodeAbi,
    ) -> Result<Rc<VakModule>, VmError> {
        let (resolved_name, module_path) = self.resolve_module_path(module_name, current_bytecode)?;
        let cache_key = fs::canonicalize(&module_path)
            .unwrap_or_else(|_| module_path.clone())
            .to_string_lossy()
            .to_string();
        if let Some(module) = self.module_cache.get(&cache_key) {
            return Ok(module.clone());
        }

        let envelope = self.load_module_abi(&module_path)?;
        let module_root = Rc::new(envelope.bytecode.clone());
        let mut child_vm = Vm::new();
        child_vm.module_cache = self.module_cache.clone();
        let _ = child_vm.run(&envelope.bytecode)?;
        self.output.push_str(&child_vm.output);
        self.module_cache.extend(child_vm.module_cache.clone());

        let mut attrs = BTreeMap::new();
        for (name, value) in child_vm.globals {
            if is_internal_binding_name(&name) {
                continue;
            }
            attrs.insert(name, adopt_module_value(value, module_root.clone()));
        }

        let module = Rc::new(VakModule {
            name: resolved_name,
            attrs,
            root: module_root,
        });
        self.module_cache.insert(cache_key, module.clone());
        Ok(module)
    }

    fn resolve_module_path(
        &self,
        module_name: &str,
        current_bytecode: &BytecodeAbi,
    ) -> Result<(String, PathBuf), VmError> {
        for candidate_name in module_name_candidates(module_name) {
            let mut relative_names = vec![candidate_name.clone()];
            let package_name = candidate_name.replace('.', std::path::MAIN_SEPARATOR_STR);
            if package_name != candidate_name {
                relative_names.push(package_name);
            }

            for search_dir in module_search_dirs(current_bytecode) {
                for relative_name in &relative_names {
                    let file_path = search_dir.join(format!("{relative_name}.vak"));
                    if file_path.exists() {
                        return Ok((candidate_name.clone(), file_path));
                    }

                    let init_path = search_dir.join(relative_name).join("__init__.vak");
                    if init_path.exists() {
                        return Ok((candidate_name.clone(), init_path));
                    }
                }
            }
        }

        Err(VmError::ModuleNotFound(module_name.to_string()))
    }

    fn load_module_abi(&self, module_path: &Path) -> Result<AbiEnvelope, VmError> {
        let abi_path = module_path.with_extension("abi.json");
        if abi_path.exists() {
            return AbiEnvelope::from_path(&abi_path)
                .map_err(|error| VmError::ImportBridgeFailed(error.to_string()));
        }

        let project_root = find_project_root().ok_or(VmError::ProjectRootNotFound)?;
        let export_script = project_root.join("runtime").join("export_abi.py");
        let temp_abi = env::temp_dir().join(format!(
            "vak_import_{}_{}.abi.json",
            std::process::id(),
            module_path
                .file_stem()
                .and_then(|name| name.to_str())
                .unwrap_or("module")
        ));

        let python_commands = python_command_candidates();
        for (program, prefix_args) in python_commands {
            let mut command = Command::new(&program);
            for arg in &prefix_args {
                command.arg(arg);
            }
            command.arg(&export_script).arg(module_path).arg("-o").arg(&temp_abi);
            command.current_dir(&project_root);
            let output = command.output();
            if let Ok(output) = output {
                if output.status.success() {
                    let envelope = AbiEnvelope::from_path(&temp_abi)
                        .map_err(|error| VmError::ImportBridgeFailed(error.to_string()))?;
                    let _ = fs::remove_file(&temp_abi);
                    return Ok(envelope);
                }
            }
        }

        Err(VmError::PythonNotFound)
    }

    fn call_builtin(
        &mut self,
        builtin: Builtin,
        args: Vec<Value>,
        kwargs: BTreeMap<String, Value>,
    ) -> Result<Value, VmError> {
        match builtin {
            Builtin::VakStr => {
                reject_kwargs("str", &kwargs)?;
                Ok(Value::Str(
                    args.first().cloned().unwrap_or(Value::Null).stringify(),
                ))
            }
            Builtin::Range => {
                reject_kwargs("range", &kwargs)?;
                let (start, stop, step) = match args.as_slice() {
                    [stop] => (0, stop.to_i64()?, 1),
                    [start, stop] => (start.to_i64()?, stop.to_i64()?, 1),
                    [start, stop, step] => (start.to_i64()?, stop.to_i64()?, step.to_i64()?),
                    _ => return Err(VmError::UnsupportedBuiltin("range arity".to_string())),
                };
                if step == 0 {
                    return Err(VmError::DivisionByZero);
                }
                let mut values = Vec::new();
                if step > 0 {
                    let mut current = start;
                    while current < stop {
                        values.push(Value::Int(current));
                        current += step;
                    }
                } else {
                    let mut current = start;
                    while current > stop {
                        values.push(Value::Int(current));
                        current += step;
                    }
                }
                Ok(Value::List(Rc::new(RefCell::new(values))))
            }
            Builtin::Len => {
                reject_kwargs("len", &kwargs)?;
                let value = args
                    .first()
                    .ok_or_else(|| VmError::UnsupportedBuiltin("len arity".to_string()))?;
                let length = match value {
                    Value::Str(text) => text.chars().count(),
                    Value::List(items) => items.borrow().len(),
                    Value::Tuple(items) => items.len(),
                    Value::Dict(items) => items.borrow().len(),
                    other => {
                        return Err(VmError::TypeMismatch {
                            expected: "sized value",
                            actual: other.type_name(),
                        })
                    }
                };
                Ok(Value::Int(length as i64))
            }
            Builtin::VakType => {
                reject_kwargs("type", &kwargs)?;
                Ok(Value::Str(args.first().cloned().unwrap_or(Value::Null).classify()))
            }
            Builtin::ToInt => {
                reject_kwargs("int", &kwargs)?;
                let value = args.first().cloned().unwrap_or(Value::Int(0));
                let converted = match value {
                    Value::Int(value) => value,
                    Value::Float(value) => value.trunc() as i64,
                    Value::Bool(value) => {
                        if value {
                            1
                        } else {
                            0
                        }
                    }
                    Value::Str(text) => {
                        text.trim()
                            .parse::<i64>()
                            .map_err(|_| VmError::TypeMismatch {
                                expected: "int-compatible string",
                                actual: "str",
                            })?
                    }
                    other => {
                        return Err(VmError::TypeMismatch {
                            expected: "int-compatible value",
                            actual: other.type_name(),
                        })
                    }
                };
                Ok(Value::Int(converted))
            }
            Builtin::ToFloat => {
                reject_kwargs("float", &kwargs)?;
                let value = args.first().cloned().unwrap_or(Value::Float(0.0));
                let converted = match value {
                    Value::Int(value) => value as f64,
                    Value::Float(value) => value,
                    Value::Bool(value) => {
                        if value {
                            1.0
                        } else {
                            0.0
                        }
                    }
                    Value::Str(text) => {
                        text.trim()
                            .parse::<f64>()
                            .map_err(|_| VmError::TypeMismatch {
                                expected: "float-compatible string",
                                actual: "str",
                            })?
                    }
                    other => {
                        return Err(VmError::TypeMismatch {
                            expected: "float-compatible value",
                            actual: other.type_name(),
                        })
                    }
                };
                Ok(Value::Float(converted))
            }
            Builtin::Print => {
                let sep = kwargs
                    .get("sep")
                    .cloned()
                    .unwrap_or_else(|| Value::Str(" ".to_string()))
                    .stringify();
                let end = kwargs
                    .get("end")
                    .cloned()
                    .unwrap_or_else(|| Value::Str("\n".to_string()))
                    .stringify();
                let line = args
                    .iter()
                    .map(Value::stringify)
                    .collect::<Vec<_>>()
                    .join(&sep);
                self.output.push_str(&line);
                self.output.push_str(&end);
                Ok(Value::Null)
            }
            Builtin::Join => {
                reject_kwargs("संयोग", &kwargs)?;
                let Some(sequence) = args.first() else {
                    return Err(VmError::UnsupportedBuiltin("संयोग arity".to_string()));
                };
                let separator = args
                    .get(1)
                    .cloned()
                    .unwrap_or_else(|| Value::Str(String::new()))
                    .stringify();
                let joined = sequence
                    .iter_items()?
                    .iter()
                    .map(Value::stringify)
                    .collect::<Vec<_>>()
                    .join(&separator);
                Ok(Value::Str(joined))
            }
            Builtin::Split => {
                reject_kwargs("विभाजन", &kwargs)?;
                let text = args
                    .first()
                    .cloned()
                    .unwrap_or(Value::Str(String::new()))
                    .stringify();
                let separator = args
                    .get(1)
                    .cloned()
                    .unwrap_or_else(|| Value::Str(" ".to_string()))
                    .stringify();
                let parts = if separator.is_empty() {
                    text.chars()
                        .map(|ch| Value::Str(ch.to_string()))
                        .collect::<Vec<_>>()
                } else {
                    text.split(&separator)
                        .map(|part| Value::Str(part.to_string()))
                        .collect::<Vec<_>>()
                };
                Ok(Value::List(Rc::new(RefCell::new(parts))))
            }
            Builtin::Strip => {
                reject_kwargs("छाँटो", &kwargs)?;
                Ok(Value::Str(
                    args.first()
                        .cloned()
                        .unwrap_or(Value::Str(String::new()))
                        .stringify()
                        .trim()
                        .to_string(),
                ))
            }
            Builtin::Upper => {
                reject_kwargs("उच्च", &kwargs)?;
                Ok(Value::Str(
                    args.first()
                        .cloned()
                        .unwrap_or(Value::Str(String::new()))
                        .stringify()
                        .to_uppercase(),
                ))
            }
            Builtin::Lower => {
                reject_kwargs("निम्न", &kwargs)?;
                Ok(Value::Str(
                    args.first()
                        .cloned()
                        .unwrap_or(Value::Str(String::new()))
                        .stringify()
                        .to_lowercase(),
                ))
            }
            Builtin::Sorted => {
                reject_kwargs("क्रमबद्ध", &kwargs)?;
                let mut items = args
                    .first()
                    .ok_or_else(|| VmError::UnsupportedBuiltin("क्रमबद्ध arity".to_string()))?
                    .iter_items()?;
                items.sort_by_key(Value::stringify);
                Ok(Value::List(Rc::new(RefCell::new(items))))
            }
            Builtin::Sum => {
                reject_kwargs("योग", &kwargs)?;
                let items = args
                    .first()
                    .ok_or_else(|| VmError::UnsupportedBuiltin("योग arity".to_string()))?
                    .iter_items()?;
                let mut total = Value::Int(0);
                for item in items {
                    total = total.add(item)?;
                }
                Ok(total)
            }
            Builtin::Max => {
                reject_kwargs("अधिकतम", &kwargs)?;
                max_or_min(args, true)
            }
            Builtin::Min => {
                reject_kwargs("न्यूनतम", &kwargs)?;
                max_or_min(args, false)
            }
            Builtin::DictKeys => {
                reject_kwargs("कुंजियाँ", &kwargs)?;
                let Some(Value::Dict(items)) = args.first() else {
                    return Err(VmError::TypeMismatch {
                        expected: "dict",
                        actual: args.first().map(Value::type_name).unwrap_or("null"),
                    });
                };
                Ok(Value::List(Rc::new(RefCell::new(
                    items.borrow().iter().map(|(key, _)| key.clone()).collect(),
                ))))
            }
            Builtin::DictValues => {
                reject_kwargs("मान", &kwargs)?;
                let Some(Value::Dict(items)) = args.first() else {
                    return Err(VmError::TypeMismatch {
                        expected: "dict",
                        actual: args.first().map(Value::type_name).unwrap_or("null"),
                    });
                };
                Ok(Value::List(Rc::new(RefCell::new(
                    items.borrow().iter().map(|(_, value)| value.clone()).collect(),
                ))))
            }
            Builtin::Sqrt => {
                reject_kwargs("वर्गमूल", &kwargs)?;
                let input = args.first().cloned().unwrap_or(Value::Int(0)).to_f64()?;
                Ok(Value::Float(input.sqrt()))
            }
            Builtin::Abs => {
                reject_kwargs("परम", &kwargs)?;
                match args.first().cloned().unwrap_or(Value::Int(0)) {
                    Value::Int(value) => Ok(Value::Int(value.abs())),
                    Value::Float(value) => Ok(Value::Float(value.abs())),
                    other => Err(VmError::TypeMismatch {
                        expected: "numeric",
                        actual: other.type_name(),
                    }),
                }
            }
            Builtin::Round => {
                reject_kwargs("round", &kwargs)?;
                let input = args.first().cloned().unwrap_or(Value::Int(0)).to_f64()?;
                Ok(Value::Int(input.round() as i64))
            }
            Builtin::Ord => {
                reject_kwargs("ord", &kwargs)?;
                let text = args
                    .first()
                    .cloned()
                    .unwrap_or(Value::Str(String::new()))
                    .stringify();
                let Some(ch) = text.chars().next() else {
                    return Err(VmError::UnsupportedBuiltin("ord empty string".to_string()));
                };
                Ok(Value::Int(ch as i64))
            }
            Builtin::Chr => {
                reject_kwargs("chr", &kwargs)?;
                let value = args.first().cloned().unwrap_or(Value::Int(0)).to_i64()?;
                let Some(ch) = char::from_u32(value as u32) else {
                    return Err(VmError::UnsupportedBuiltin("chr range".to_string()));
                };
                Ok(Value::Str(ch.to_string()))
            }
            Builtin::Bool => {
                reject_kwargs("bool", &kwargs)?;
                Ok(Value::Bool(
                    args.first().cloned().unwrap_or(Value::Null).truthy(),
                ))
            }
            Builtin::List => {
                reject_kwargs("list", &kwargs)?;
                if let Some(value) = args.first() {
                    Ok(Value::List(Rc::new(RefCell::new(value.iter_items()?))))
                } else {
                    Ok(Value::List(Rc::new(RefCell::new(Vec::new()))))
                }
            }
            Builtin::Dict => {
                reject_kwargs("dict", &kwargs)?;
                if args.is_empty() {
                    return Ok(Value::Dict(Rc::new(RefCell::new(Vec::new()))));
                }
                let pairs_source = args[0].iter_items()?;
                let mut pairs = Vec::new();
                for item in pairs_source {
                    let Value::Tuple(values) = item else {
                        return Err(VmError::TypeMismatch {
                            expected: "sequence of key/value tuples",
                            actual: item.type_name(),
                        });
                    };
                    if values.len() != 2 {
                        return Err(VmError::TypeMismatch {
                            expected: "2-item tuple",
                            actual: "tuple",
                        });
                    }
                    pairs.push((values[0].clone(), values[1].clone()));
                }
                Ok(Value::Dict(Rc::new(RefCell::new(pairs))))
            }
            Builtin::Callable => {
                reject_kwargs("callable", &kwargs)?;
                Ok(Value::Bool(matches!(
                    args.first(),
                    Some(Value::FunctionRef { .. })
                        | Some(Value::Builtin(_))
                        | Some(Value::Class(_))
                        | Some(Value::BoundMethod { .. })
                )))
            }
            Builtin::MatchException => {
                reject_kwargs("__match_exception__", &kwargs)?;
                if args.len() != 2 {
                    return Err(VmError::UnsupportedBuiltin(
                        "__match_exception__ arity".to_string(),
                    ));
                }
                let exception_text = args[0].clone().stringify();
                let handler_text = args[1].clone().stringify();
                let handler_trimmed = handler_text.trim();
                if handler_trimmed.is_empty() || handler_trimmed == "_" {
                    return Ok(Value::Bool(true));
                }
                if handler_trimmed.ends_with("Error") || handler_trimmed.ends_with("Exception") {
                    let lowered = exception_text.to_lowercase();
                    let matches = match handler_trimmed {
                        "ZeroDivisionError" => lowered.contains("division by zero"),
                        "TypeError" => {
                            lowered.contains("type mismatch")
                                || lowered.contains("unsupported binary operation")
                                || lowered.contains("unsupported unary operation")
                        }
                        _ => exception_text.contains(handler_trimmed),
                    };
                    return Ok(Value::Bool(matches));
                }
                Ok(Value::Bool(true))
            }
            Builtin::Unsupported(name) => Err(VmError::UnsupportedBuiltin(name)),
        }
    }
}

fn reject_kwargs(name: &str, kwargs: &BTreeMap<String, Value>) -> Result<(), VmError> {
    if kwargs.is_empty() {
        Ok(())
    } else {
        Err(VmError::UnsupportedBuiltin(format!("{name} kwargs")))
    }
}

fn is_internal_binding_name(name: &str) -> bool {
    name.starts_with("__imported_module_") || (name.starts_with('<') && name.ends_with('>'))
}

fn module_name_candidates(module_name: &str) -> Vec<String> {
    let aliases = BTreeMap::from([
        ("गणित", "ganit"),
        ("गणित_विस्तारित", "ganit_vistarit"),
        ("भाषा_प्रसादन", "bhasha_prasadan"),
        ("तर्क_शास्त्र", "tarka_shastra"),
        ("संग्रह", "sangrah"),
        ("संग्रह_विस्तारित", "sangrah_vistarit"),
        ("डेटा_संग्रह", "data_sangrah"),
        ("कंटेनर_संग्रह", "container_sangrah"),
        ("मैट्रिक्स_गणित", "matrix_ganit"),
        ("संभावना", "sambhavana"),
        ("उपयोगिता", "upayogita"),
        ("रेखा_गणित", "rekha_ganit"),
        ("धागा", "dhaaga"),
        ("फाइल", "file"),
        ("कूटलेख", "kootlekh"),
        ("नियमित", "niyamit"),
        ("मूल", "mool"),
        ("यादृच्छ", "yadricha"),
        ("उन्नत_सांख्यिकी", "unnata_sankhyiki"),
    ]);

    let mut candidates = vec![module_name.to_string()];
    if let Some(alias) = aliases.get(module_name) {
        if !candidates.iter().any(|candidate| candidate == alias) {
            candidates.push((*alias).to_string());
        }
    }
    candidates
}

fn module_search_dirs(current_bytecode: &BytecodeAbi) -> Vec<PathBuf> {
    let mut search_dirs = Vec::new();
    let mut add_dir = |path: PathBuf| {
        if !search_dirs.iter().any(|existing| existing == &path) {
            search_dirs.push(path);
        }
    };

    if let Some(source_path) = &current_bytecode.source_path {
        if let Some(parent) = Path::new(source_path).parent() {
            add_dir(parent.to_path_buf());
        }
    }

    if let Ok(current_dir) = env::current_dir() {
        add_dir(current_dir.clone());
        add_dir(current_dir.join("वाक्_ग्रंथालय"));
        for ancestor in current_dir.ancestors() {
            let runtime_dir = ancestor.join("runtime");
            if runtime_dir.exists() {
                add_dir(runtime_dir.clone());
                add_dir(runtime_dir.join("stdlib"));
            }
            let project_dir = ancestor.to_path_buf();
            add_dir(project_dir.join("वाक्_ग्रंथालय"));
        }
    }

    if let Ok(exe_path) = env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            for ancestor in exe_dir.ancestors() {
                let runtime_dir = ancestor.join("runtime");
                if runtime_dir.exists() {
                    add_dir(runtime_dir.clone());
                    add_dir(runtime_dir.join("stdlib"));
                }
            }
        }
    }

    if let Ok(stdlib_dir) = env::var("VAK_STDLIB_DIR") {
        add_dir(PathBuf::from(stdlib_dir));
    }

    search_dirs
}

fn find_project_root() -> Option<PathBuf> {
    if let Ok(root) = env::var("VAK_PROJECT_ROOT") {
        let root = PathBuf::from(root);
        if root.join("runtime").join("export_abi.py").exists() {
            return Some(root);
        }
    }

    let mut candidates = Vec::new();
    if let Ok(current_dir) = env::current_dir() {
        candidates.push(current_dir);
    }
    if let Ok(exe_path) = env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            candidates.push(exe_dir.to_path_buf());
        }
    }

    for start in candidates {
        for ancestor in start.ancestors() {
            let export_script = ancestor.join("runtime").join("export_abi.py");
            if export_script.exists() {
                return Some(ancestor.to_path_buf());
            }
        }
    }

    None
}

fn python_command_candidates() -> Vec<(String, Vec<String>)> {
    let mut candidates = Vec::new();
    if let Ok(python) = env::var("VAK_PYTHON") {
        if !python.trim().is_empty() {
            candidates.push((python, Vec::new()));
        }
    }
    candidates.push(("python".to_string(), Vec::new()));
    candidates.push(("py".to_string(), vec!["-3".to_string()]));
    candidates
}

fn adopt_module_value(value: Value, module_root: Rc<BytecodeAbi>) -> Value {
    match value {
        Value::FunctionRef { name, is_async, .. } => Value::FunctionRef {
            name,
            is_async,
            root: Some(module_root),
        },
        Value::Class(class) => Value::Class(Rc::new(VakClass {
            name: class.name.clone(),
            methods: class.methods.clone(),
            root: Some(module_root),
        })),
        other => other,
    }
}

fn get_attr(object: Value, attr_name: &str) -> Result<Value, VmError> {
    match object {
        Value::Instance(instance) => {
            let instance_ref = instance.borrow();
            if let Some(value) = instance_ref.attrs.get(attr_name) {
                Ok(value.clone())
            } else if instance_ref.klass.methods.contains_key(attr_name) {
                Ok(Value::BoundMethod {
                    object: Box::new(Value::Instance(instance.clone())),
                    method_name: attr_name.to_string(),
                })
            } else {
                Err(VmError::AttributeNotFound {
                    target: instance_ref.klass.name.clone(),
                    attribute: attr_name.to_string(),
                })
            }
        }
        Value::Module(module) => module.attrs.get(attr_name).cloned().ok_or_else(|| VmError::AttributeNotFound {
            target: format!("module {}", module.name),
            attribute: attr_name.to_string(),
        }),
        Value::Class(class) => {
            if class.methods.contains_key(attr_name) {
                Ok(Value::FunctionRef {
                    name: attr_name.to_string(),
                    is_async: false,
                    root: class.root.clone(),
                })
            } else {
                Err(VmError::AttributeNotFound {
                    target: format!("class {}", class.name),
                    attribute: attr_name.to_string(),
                })
            }
        }
        other => Err(VmError::AttributeNotFound {
            target: other.type_name().to_string(),
            attribute: attr_name.to_string(),
        }),
    }
}

fn set_attr(object: &Value, attr_name: &str, value: Value) -> Result<(), VmError> {
    match object {
        Value::Instance(instance) => {
            instance.borrow_mut().attrs.insert(attr_name.to_string(), value);
            Ok(())
        }
        other => Err(VmError::AttributeNotFound {
            target: other.type_name().to_string(),
            attribute: attr_name.to_string(),
        }),
    }
}

fn max_or_min(args: Vec<Value>, want_max: bool) -> Result<Value, VmError> {
    let mut candidates = if args.len() == 1 {
        args[0].iter_items()?
    } else {
        args
    };
    let Some(mut best) = candidates.pop() else {
        return Err(VmError::UnsupportedBuiltin("empty candidate set".to_string()));
    };
    for candidate in candidates {
        let better = if want_max {
            best.cmp_lt(&candidate)?
        } else {
            candidate.cmp_lt(&best)?
        };
        if better {
            best = candidate;
        }
    }
    Ok(best)
}

fn pop(stack: &mut Vec<Value>) -> Result<Value, VmError> {
    stack.pop().ok_or(VmError::StackUnderflow)
}

fn pop_n(stack: &mut Vec<Value>, count: usize) -> Result<Vec<Value>, VmError> {
    if stack.len() < count {
        return Err(VmError::StackUnderflow);
    }
    let start = stack.len() - count;
    Ok(stack.drain(start..).collect())
}

fn pop_kwargs(stack: &mut Vec<Value>) -> Result<BTreeMap<String, Value>, VmError> {
    let actual = stack.last().map(Value::type_name).unwrap_or("null");
    let Value::Dict(items) = pop(stack)? else {
        return Err(VmError::TypeMismatch {
            expected: "dict",
            actual,
        });
    };
    let mut kwargs = BTreeMap::new();
    for (key, value) in items.borrow().iter() {
        let Value::Str(name) = key else {
            return Err(VmError::InvalidKeywordKey(key.type_name()));
        };
        kwargs.insert(name.clone(), value.clone());
    }
    Ok(kwargs)
}

fn index_get(object: &Value, index: &Value) -> Result<Value, VmError> {
    match object {
        Value::List(items) => {
            let idx = normalized_index(items.borrow().len(), index)?;
            Ok(items.borrow()[idx].clone())
        }
        Value::Tuple(items) => {
            let idx = normalized_index(items.len(), index)?;
            Ok(items[idx].clone())
        }
        Value::Str(text) => {
            let chars = text.chars().collect::<Vec<_>>();
            let idx = normalized_index(chars.len(), index)?;
            Ok(Value::Str(chars[idx].to_string()))
        }
        Value::Dict(items) => {
            for (key, value) in items.borrow().iter() {
                if key.cmp_eq(index) {
                    return Ok(value.clone());
                }
            }
            Err(VmError::IndexOutOfRange)
        }
        other => Err(VmError::TypeMismatch {
            expected: "indexable value",
            actual: other.type_name(),
        }),
    }
}

fn index_set(object: &Value, index: &Value, value: Value) -> Result<(), VmError> {
    match object {
        Value::List(items) => {
            let idx = normalized_index(items.borrow().len(), index)?;
            items.borrow_mut()[idx] = value;
            Ok(())
        }
        Value::Dict(items) => {
            let mut items_ref = items.borrow_mut();
            if let Some((_, existing_value)) = items_ref.iter_mut().find(|(key, _)| key.cmp_eq(index)) {
                *existing_value = value;
            } else {
                items_ref.push((index.clone(), value));
            }
            Ok(())
        }
        other => Err(VmError::TypeMismatch {
            expected: "mutable indexed value",
            actual: other.type_name(),
        }),
    }
}

fn normalized_index(len: usize, index: &Value) -> Result<usize, VmError> {
    let raw = match index {
        Value::Int(value) => *value,
        Value::Float(value) => value.trunc() as i64,
        other => return Err(VmError::InvalidIndexType(other.type_name())),
    };
    let adjusted = if raw < 0 { len as i64 + raw } else { raw };
    if adjusted < 0 || adjusted as usize >= len {
        return Err(VmError::IndexOutOfRange);
    }
    Ok(adjusted as usize)
}

fn find_function<'a>(bytecode: &'a BytecodeAbi, name: &str) -> Option<&'a BytecodeAbi> {
    if let Some(function) = bytecode.functions.get(name) {
        return Some(function);
    }
    for function in bytecode.functions.values() {
        if let Some(found) = find_function(function, name) {
            return Some(found);
        }
    }
    None
}

fn read_u16(code: &[u8], offset: usize) -> Result<u16, VmError> {
    let hi = *code.get(offset).ok_or(VmError::InvalidJump(offset as isize))? as u16;
    let lo = *code
        .get(offset + 1)
        .ok_or(VmError::InvalidJump((offset + 1) as isize))? as u16;
    Ok((hi << 8) | lo)
}

fn read_i16(code: &[u8], offset: usize) -> Result<i16, VmError> {
    Ok(read_u16(code, offset)? as i16)
}

fn jump_target(pc: usize, instruction_size: usize, offset: isize, code_len: usize) -> Result<usize, VmError> {
    let target = pc as isize + instruction_size as isize + offset;
    if target < 0 || target as usize > code_len {
        return Err(VmError::InvalidJump(target));
    }
    Ok(target as usize)
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;

    use crate::abi::{AbiEnvelope, AbiValue, BytecodeAbi};

    use super::{Value, Vm};

    fn empty_bytecode(name: &str) -> BytecodeAbi {
        BytecodeAbi {
            name: name.to_string(),
            source_path: None,
            code: Vec::new(),
            constants: Vec::new(),
            var_names: Vec::new(),
            param_names: Vec::new(),
            functions: BTreeMap::new(),
            defaults: Vec::new(),
            varargs_name: None,
            num_params: 0,
            global_names: Vec::new(),
            type_hints: BTreeMap::new(),
            is_async: false,
            vibhakti_signature: None,
        }
    }

    #[test]
    fn executes_basic_arithmetic_program() {
        let envelope = AbiEnvelope::parse_str(
            r#"
            {
              "format": "vak_bytecode_abi",
              "version": 1,
              "bytecode": {
                "name": "<module>",
                "code": [1,0,0,1,0,1,16,112,255],
                "constants": [
                  {"kind":"int","value":40},
                  {"kind":"int","value":2}
                ],
                "var_names": [],
                "param_names": [],
                "functions": {},
                "defaults": [],
                "varargs_name": null,
                "num_params": 0,
                "global_names": [],
                "type_hints": {},
                "is_async": false,
                "vibhakti_signature": null
              }
            }
            "#,
        )
        .expect("valid ABI JSON");

        let result = Vm::run_envelope(&envelope).expect("program executes");
        assert_eq!(result.output, "42");
        assert!(result.top.is_none());
    }

    #[test]
    fn executes_user_function_calls_with_defaults_and_kwargs() {
        let mut add_bc = empty_bytecode("mul_add");
        add_bc.code = vec![0x02, 0x00, 0x02, 0x01, 0x12, 0x02, 0x02, 0x10, 0x51];
        add_bc.var_names = vec!["x".to_string(), "y".to_string(), "z".to_string()];
        add_bc.param_names = add_bc.var_names.clone();
        add_bc.num_params = 3;
        add_bc.defaults = vec![
            AbiValue::Null,
            AbiValue::Int { value: 2 },
            AbiValue::Int { value: 1 },
        ];

        let mut module = empty_bytecode("<module>");
        module.var_names = vec!["mul_add".to_string()];
        module.constants = vec![
            AbiValue::CallableRef {
                callable_kind: "function".to_string(),
                name: "mul_add".to_string(),
                is_async: Some(false),
            },
            AbiValue::Int { value: 5 },
            AbiValue::Int { value: 3 },
            AbiValue::Str {
                value: "z".to_string(),
            },
            AbiValue::Str {
                value: "\n".to_string(),
            },
        ];
        module.functions.insert("mul_add".to_string(), add_bc);
        module.code = vec![
            0x01, 0x00, 0x00, 0x03, 0x00,
            0x02, 0x00, 0x01, 0x00, 0x01, 0x50, 0x01, 0x70,
            0x01, 0x00, 0x04, 0x70,
            0x02, 0x00, 0x01, 0x00, 0x01, 0x01, 0x00, 0x02, 0x01, 0x00, 0x03, 0x61, 0x01, 0x56, 0x01, 0x70,
            0x01, 0x00, 0x04, 0x70,
            0xff,
        ];

        let mut vm = Vm::new();
        let result = vm.run(&module).expect("function calls execute");
        assert_eq!(result.output, "11\n13\n");
    }

    #[test]
    fn value_stringify_matches_pythonish_style() {
        let list = Value::List(std::rc::Rc::new(std::cell::RefCell::new(vec![
            Value::Int(1),
            Value::Bool(true),
            Value::Str("vak".to_string()),
        ])));
        assert_eq!(list.to_string(), "[1, True, vak]");
    }
}
