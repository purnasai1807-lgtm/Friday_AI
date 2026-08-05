//! MemoryBackend trait for all storage backends.

use friday_core::{FridayError, RetrievalResult};
use serde_json::Value;

pub trait MemoryBackend: Send + Sync {
    fn backend_id(&self) -> &str;
    fn store(
        &self,
        content: &str,
        source: &str,
        metadata: Option<&Value>,
    ) -> Result<String, FridayError>;
    fn retrieve(
        &self,
        query: &str,
        top_k: usize,
    ) -> Result<Vec<RetrievalResult>, FridayError>;
    fn delete(&self, doc_id: &str) -> Result<bool, FridayError>;
    fn clear(&self) -> Result<(), FridayError>;
    fn count(&self) -> Result<usize, FridayError>;
}
