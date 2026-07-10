"""
front_server — F5: Aurel Front v1, the one door between the UI and the kernel.

A stdlib HTTP + WebSocket server whose only job is to map three route classes onto
the existing backend with no other executor: read projections (`GET /read/{model}`),
the single mutation (`POST /proposals` → dispatcher → conversation turn /
`runtime.submit`), and a WS stream. The server is not constructed when
`AUREL_FRONT_SERVER` is OFF — a flag-off runtime is byte-identical.
"""
from __future__ import annotations

from .approval_gates import DeferredApprovalGate, PreDecidedApprovalGate
from .approval_inbox import ApprovalInbox, PendingApproval
from .conversation import (
    ConversationEngine,
    ConversationReply,
    ConversationTurn,
    HistoryEntry,
    ReplyMode,
    RoomHistoryProjection,
    rooms_from_trace,
)
from .proposal_dispatcher import (
    KIND_ACT,
    KIND_CONVERSE,
    KIND_DECIDE,
    ProposalDispatcher,
    ProposalRejected,
)
from .aureleu import (
    AurelEUDispatcher,
    DispatchAuthorization,
    PersonaResolution,
    resolve_mode,
)
from .board import BoardDecision, BoardJournal, BoardJournalEntry
from .hq_command import CLAIMS_WATCHTOWER_LIVE, HQCommandReadModel
from .library import CLAIMS_LIBRARY_TIME_TRAVEL, LibraryReadModel
from .read_models import LiveReadModels, ReadModelError
from .routes import ROUTES, Route, match_route, mutation_routes
from .server import (
    FrontApp,
    FrontServer,
    FrontServerDisabled,
    create_front_server,
    flag_enabled,
)
from .signal import SignalMessage
from .workops import (
    CLAIMS_WORKOPS_AI_EDITOR,
    CLAIMS_WORKOPS_CODE_LIVE,
    CLAIMS_WORKOPS_TERMINAL_LIVE,
    WorkOpsChatReadModel,
    WorkOpsMessage,
    WorkOpsTask,
    workops_room,
)
from .websocket import (
    WebSocketConnection,
    WebSocketError,
    build_frame,
    compute_accept_key,
    parse_frame,
)

__all__ = [
    "ROUTES",
    "Route",
    "match_route",
    "mutation_routes",
    "ProposalDispatcher",
    "ProposalRejected",
    "LiveReadModels",
    "ReadModelError",
    "LibraryReadModel",
    "CLAIMS_LIBRARY_TIME_TRAVEL",
    "HQCommandReadModel",
    "CLAIMS_WATCHTOWER_LIVE",
    "BoardDecision",
    "BoardJournal",
    "BoardJournalEntry",
    "AurelEUDispatcher",
    "DispatchAuthorization",
    "PersonaResolution",
    "resolve_mode",
    "KIND_CONVERSE",
    "KIND_ACT",
    "KIND_DECIDE",
    "FrontServer",
    "FrontApp",
    "FrontServerDisabled",
    "create_front_server",
    "flag_enabled",
    "compute_accept_key",
    "build_frame",
    "parse_frame",
    "WebSocketConnection",
    "WebSocketError",
    "ConversationEngine",
    "ConversationTurn",
    "ConversationReply",
    "ReplyMode",
    "RoomHistoryProjection",
    "HistoryEntry",
    "rooms_from_trace",
    "SignalMessage",
    "WorkOpsMessage",
    "WorkOpsChatReadModel",
    "WorkOpsTask",
    "workops_room",
    "CLAIMS_WORKOPS_CODE_LIVE",
    "CLAIMS_WORKOPS_TERMINAL_LIVE",
    "CLAIMS_WORKOPS_AI_EDITOR",
    "ApprovalInbox",
    "PendingApproval",
    "DeferredApprovalGate",
    "PreDecidedApprovalGate",
]
