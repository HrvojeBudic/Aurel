"""
corp — the Business Plane domain (F7): clients, jobs, and the klijent-nula seed.

F7 wraps the mature governance machinery in a thin business layer. A **job**
(posao) is the business wrapper around one or more mandates; a **client** is the
party the work is for. The domain does **not** grant authority — authority stays
the mandate (F6), enforced fail-closed in `runtime.submit`. Jobs reference mandates
by id (reused from the existing `MandateRegistry`, never copied), and the registry
validates those references at build time, fail-closed.

Additive behind `AUREL_CORP` (default OFF ⇒ no corp read-model / cost bucket,
byte-identical F6 world). This module is the F7.0 data model + resolution; cost
attribution (F7.1), Watchtower (F7.3), Evidence Vault (F7.4), and the CORP surface
(F7.5+) build on it.
"""
from __future__ import annotations

from .budget_governance import ClientBudgetView
from .cost import CostAttributionView
from .default import (
    CLIENT_ZERO_ID,
    JOB_ZERO_ID,
    client_zero,
    client_zero_job,
    default_corp_registry,
)
from .domain import ClientRecord, JobRecord, JobStatus, flag_enabled
from .evidence_vault import EvidenceVaultQuery
from .kpi import ReflexFlywheelView
from .registry import (
    ClientNotFound,
    CorpRegistry,
    CorpValidationError,
    JobNotFound,
)
from .risk_register import (
    RiskEntry,
    RiskRegisterProjection,
    RiskStatus,
    record_risk,
)
from .watchtower import (
    AlertKind,
    AlertSeverity,
    WatchtowerAlert,
    derive_alerts,
    live_feed,
)
from .watchtower import flag_enabled as watchtower_flag_enabled
from .wizard import EnvironmentTemplate, ImpactReport, SampleAction, what_if

__all__ = [
    "ClientRecord",
    "JobRecord",
    "JobStatus",
    "flag_enabled",
    "CorpRegistry",
    "CorpValidationError",
    "ClientNotFound",
    "JobNotFound",
    "client_zero",
    "client_zero_job",
    "default_corp_registry",
    "CLIENT_ZERO_ID",
    "JOB_ZERO_ID",
    "CostAttributionView",
    "ClientBudgetView",
    "EvidenceVaultQuery",
    "ReflexFlywheelView",
    "WatchtowerAlert",
    "AlertKind",
    "AlertSeverity",
    "derive_alerts",
    "live_feed",
    "watchtower_flag_enabled",
    "EnvironmentTemplate",
    "SampleAction",
    "ImpactReport",
    "what_if",
    "RiskEntry",
    "RiskStatus",
    "RiskRegisterProjection",
    "record_risk",
]
