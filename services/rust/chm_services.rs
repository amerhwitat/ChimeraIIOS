pub enum ServiceState { Inactive, Starting, Active, Stopping, Failed }
#[derive(Clone, Debug)]
pub struct ServiceDescriptor { pub id:String, pub platform:String, pub backend:String, pub capabilities:Vec<String> }
pub fn can_transition(a:&ServiceState,b:&ServiceState)->bool { matches!((a,b),(ServiceState::Inactive,ServiceState::Starting)|(ServiceState::Starting,ServiceState::Active)|(ServiceState::Starting,ServiceState::Failed)|(ServiceState::Active,ServiceState::Stopping)|(ServiceState::Stopping,ServiceState::Inactive)|(ServiceState::Failed,ServiceState::Starting)) }
