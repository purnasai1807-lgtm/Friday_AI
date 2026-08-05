//! PyO3 bindings for engine types.

use crate::core::PyMessage;
use friday_engine::InferenceEngine;
use pyo3::prelude::*;

/// Wraps the Engine enum (static dispatch internally, opaque to Python).
#[pyclass(name = "Engine")]
pub struct PyEngine {
    pub inner: friday_engine::Engine,
}

#[pymethods]
impl PyEngine {
    /// Create an engine by key (e.g. "ollama", "vllm", "sglang", "llamacpp",
    /// "mlx", "lmstudio", "exo", "nexa", "uzu", "apple_fm").
    #[new]
    #[pyo3(signature = (engine_key="ollama", host=None))]
    fn new(engine_key: &str, host: Option<&str>) -> PyResult<Self> {
        let engine = match engine_key {
            "ollama" => friday_engine::Engine::Ollama(
                friday_engine::OllamaEngine::new(
                    host.unwrap_or("http://localhost:11434"),
                    120.0,
                ),
            ),
            "vllm" => friday_engine::Engine::Vllm(
                friday_engine::OpenAICompatEngine::vllm(
                    host.unwrap_or("http://localhost:8000"),
                ),
            ),
            "sglang" => friday_engine::Engine::Sglang(
                friday_engine::OpenAICompatEngine::sglang(
                    host.unwrap_or("http://localhost:30000"),
                ),
            ),
            "llamacpp" => friday_engine::Engine::LlamaCpp(
                friday_engine::OpenAICompatEngine::llamacpp(
                    host.unwrap_or("http://localhost:8080"),
                ),
            ),
            "mlx" => friday_engine::Engine::Mlx(
                friday_engine::OpenAICompatEngine::mlx(
                    host.unwrap_or("http://localhost:8080"),
                ),
            ),
            "lmstudio" => friday_engine::Engine::LmStudio(
                friday_engine::OpenAICompatEngine::lmstudio(
                    host.unwrap_or("http://localhost:1234"),
                ),
            ),
            "exo" => friday_engine::Engine::Exo(
                friday_engine::OpenAICompatEngine::exo(
                    host.unwrap_or("http://localhost:52415"),
                ),
            ),
            "nexa" => friday_engine::Engine::Nexa(
                friday_engine::OpenAICompatEngine::nexa(
                    host.unwrap_or("http://localhost:18181"),
                ),
            ),
            "uzu" => friday_engine::Engine::Uzu(
                friday_engine::OpenAICompatEngine::uzu(
                    host.unwrap_or("http://localhost:8080"),
                ),
            ),
            "apple_fm" => friday_engine::Engine::AppleFm(
                friday_engine::OpenAICompatEngine::apple_fm(
                    host.unwrap_or("http://localhost:8079"),
                ),
            ),
            "vllm_native" => friday_engine::Engine::VLLM(
                friday_engine::VLLMEngine::new(
                    host.unwrap_or("http://localhost"),
                    8000,
                    None,
                    120.0,
                ),
            ),
            "sglang_native" => friday_engine::Engine::SGLang(
                friday_engine::SGLangEngine::new(
                    host.unwrap_or("http://localhost"),
                    30000,
                    120.0,
                ),
            ),
            "llamacpp_native" => friday_engine::Engine::LlamaCppNative(
                friday_engine::LlamaCppEngine::new(
                    host.unwrap_or("http://localhost"),
                    8080,
                    120.0,
                ),
            ),
            other => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                    format!("Unknown engine: {}", other),
                ));
            }
        };
        Ok(Self { inner: engine })
    }

    fn engine_id(&self) -> &str {
        self.inner.engine_id()
    }

    fn variant_key(&self) -> &str {
        self.inner.variant_key()
    }

    fn health(&self) -> bool {
        self.inner.health()
    }

    fn list_models(&self) -> PyResult<Vec<String>> {
        self.inner
            .list_models()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    #[pyo3(signature = (messages, model, temperature=0.7, max_tokens=1024))]
    fn generate(
        &self,
        messages: Vec<PyMessage>,
        model: &str,
        temperature: f64,
        max_tokens: i64,
    ) -> PyResult<String> {
        let core_msgs: Vec<friday_core::Message> =
            messages.iter().map(|m| m.to_core()).collect();
        let result = self
            .inner
            .generate(&core_msgs, model, temperature, max_tokens, None)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).unwrap_or_default())
    }

    fn __repr__(&self) -> String {
        format!("Engine({})", self.inner.variant_key())
    }
}

/// Convenience alias for backward compatibility.
#[pyclass(name = "OllamaEngine")]
pub struct PyOllamaEngine {
    inner: friday_engine::OllamaEngine,
}

#[pymethods]
impl PyOllamaEngine {
    #[new]
    #[pyo3(signature = (host="http://localhost:11434", timeout=120.0))]
    fn new(host: &str, timeout: f64) -> Self {
        Self {
            inner: friday_engine::OllamaEngine::new(host, timeout),
        }
    }

    fn engine_id(&self) -> &str {
        self.inner.engine_id()
    }

    fn health(&self) -> bool {
        self.inner.health()
    }

    fn list_models(&self) -> PyResult<Vec<String>> {
        self.inner
            .list_models()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))
    }

    #[pyo3(signature = (messages, model, temperature=0.7, max_tokens=1024))]
    fn generate(
        &self,
        messages: Vec<PyMessage>,
        model: &str,
        temperature: f64,
        max_tokens: i64,
    ) -> PyResult<String> {
        let core_msgs: Vec<friday_core::Message> =
            messages.iter().map(|m| m.to_core()).collect();
        let result = self
            .inner
            .generate(&core_msgs, model, temperature, max_tokens, None)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(serde_json::to_string(&result).unwrap_or_default())
    }
}
