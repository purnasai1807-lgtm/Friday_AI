//! OjAgent trait — interface for all agent implementations.

use friday_core::{AgentContext, AgentResult, FridayError};

/// Core agent trait for all Friday agents.
///
/// Renamed from `Agent` to `OjAgent` to avoid collision with `rig::agent::Agent`.
/// Async to support rig-core's async model.
#[async_trait::async_trait]
pub trait OjAgent: Send + Sync {
    fn agent_id(&self) -> &str;
    fn accepts_tools(&self) -> bool {
        false
    }
    async fn run(
        &self,
        input: &str,
        context: Option<&AgentContext>,
    ) -> Result<AgentResult, FridayError>;
}
