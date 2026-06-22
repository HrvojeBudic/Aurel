"""Enumerations for the Tool / Plugin Manifest domain (P1.3.0)."""
from __future__ import annotations

from enum import Enum


class PluginOrigin(str, Enum):
    BUILTIN = "builtin"
    LOCAL = "local"
    EXTERNAL = "external"
    GENERATED = "generated"
    EXPERIMENTAL = "experimental"
    IMPORTED = "imported"
    UNKNOWN = "unknown"


class TrustLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"


class PluginStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    INVALID = "invalid"
    QUARANTINED = "quarantined"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class ToolCategory(str, Enum):
    FILESYSTEM = "filesystem"
    CODE = "code"
    TERMINAL = "terminal"
    GIT = "git"
    TEST = "test"
    MODEL = "model"
    MEMORY = "memory"
    CALENDAR = "calendar"
    EMAIL = "email"
    WEB = "web"
    BROWSER = "browser"
    DATABASE = "database"
    ENVIRONMENT = "environment"
    EVALUATION = "evaluation"
    SECURITY = "security"
    ARTIFACT = "artifact"
    COMMUNICATION = "communication"


class CapabilityType(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    TRANSFORM = "transform"
    ANALYZE = "analyze"
    RETRIEVE = "retrieve"
    SEND = "send"
    SCHEDULE = "schedule"
    SIMULATE = "simulate"
    VERIFY = "verify"
    EVALUATE = "evaluate"
    COMPILE = "compile"
    SEARCH = "search"
    OBSERVE = "observe"
    PROPOSE = "propose"


class SideEffectType(str, Enum):
    NONE = "none"
    LOCAL_READ = "local_read"
    LOCAL_WRITE = "local_write"
    EXTERNAL_READ = "external_read"
    EXTERNAL_WRITE = "external_write"
    NETWORK = "network"
    SECRET_ACCESS = "secret_access"
    PROCESS_EXECUTION = "process_execution"
    STATE_CHANGE = "state_change"


class RiskClass(str, Enum):
    R0 = "R0"
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"
    R6 = "R6"


_HIGH_RISK_CLASSES = frozenset({RiskClass.R4, RiskClass.R5, RiskClass.R6})


def is_high_risk_class(risk: RiskClass) -> bool:
    return risk in _HIGH_RISK_CLASSES


class Reversibility(str, Enum):
    NONE = "none"
    REVERSIBLE = "reversible"
    PARTIALLY_REVERSIBLE = "partially_reversible"
    IRREVERSIBLE = "irreversible"
    DRAFT_ONLY = "draft_only"
    UNKNOWN = "unknown"


class DataAccessType(str, Enum):
    NONE = "none"
    LOCAL_PROJECT = "local_project"
    LOCAL_SENSITIVE = "local_sensitive"
    MEMORY = "memory"
    SECRETS = "secrets"
    EXTERNAL = "external"
    OPERATOR_PRIVATE = "operator_private"
    UNKNOWN = "unknown"


class ExecutionEnvironment(str, Enum):
    RUNTIME = "runtime"
    SANDBOX = "sandbox"
    LOCAL_PROCESS = "local_process"
    EXTERNAL_SERVICE = "external_service"
    MODEL_PROVIDER = "model_provider"
    MANUAL_ONLY = "manual_only"
    UNKNOWN = "unknown"


class TraceLevel(str, Enum):
    NONE = "none"
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    FORENSIC = "forensic"


class CapabilityStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    INVALID = "invalid"
    QUARANTINED = "quarantined"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class RegistryEntryStatus(str, Enum):
    REGISTERED = "registered"
    DISABLED = "disabled"
    INVALID = "invalid"
    QUARANTINED = "quarantined"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class ConfidenceSeed(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DataResidency(str, Enum):
    LOCAL = "local"
    PROJECT = "project"
    REGIONAL = "regional"
    REMOTE = "remote"
    UNKNOWN = "unknown"


class NetworkPolicy(str, Enum):
    NONE = "none"
    LOCAL_ONLY = "local_only"
    ALLOWLISTED = "allowlisted"
    UNRESTRICTED = "unrestricted"
    UNKNOWN = "unknown"


class FilesystemPolicy(str, Enum):
    NONE = "none"
    READ_ONLY = "read_only"
    WORKSPACE_SCOPED = "workspace_scoped"
    UNRESTRICTED = "unrestricted"
    UNKNOWN = "unknown"


class SecretPolicy(str, Enum):
    NONE = "none"
    FORBIDDEN = "forbidden"
    OPERATOR_ONLY = "operator_only"
    ALLOWLISTED = "allowlisted"
    UNKNOWN = "unknown"


class ToolRole(str, Enum):
    PERCEPTION = "perception"
    COGNITION = "cognition"
    ACTION = "action"
    VERIFICATION = "verification"
    MEMORY = "memory"
    ENVIRONMENT = "environment"
    GOVERNANCE = "governance"


class StateDeltaType(str, Enum):
    NONE = "none"
    READ_ONLY_OBSERVATION = "read_only_observation"
    LOCAL_STATE_CHANGE = "local_state_change"
    EXTERNAL_STATE_CHANGE = "external_state_change"
    MEMORY_STATE_CHANGE = "memory_state_change"
    ENVIRONMENT_STATE_CHANGE = "environment_state_change"
    GOVERNANCE_STATE_CHANGE = "governance_state_change"
    UNKNOWN = "unknown"


class DriftRisk(str, Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class ExternalityLevel(str, Enum):
    NONE = "none"
    LOCAL_ONLY = "local_only"
    LOCAL_SENSITIVE = "local_sensitive"
    EXTERNAL_READ = "external_read"
    EXTERNAL_WRITE = "external_write"
    IRREVERSIBLE_EXTERNAL = "irreversible_external"
    UNKNOWN = "unknown"
