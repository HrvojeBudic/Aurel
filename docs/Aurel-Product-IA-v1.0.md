# Aurel Product IA v1.0

**Version:** 1.0  
**Status:** Council-approved canonical Information Architecture (2026-07-06)  
**Governing Principles:**
- Only six primary screens exist.
- Every screen, module, and submodule is a governed projection over the single durable runtime (no duplicate state).
- AurelEU is the sole component allowed to fluidly change roles and dispatch legislation-carrying agents.
- All surfaces must expose trace, governance status, pending approvals, provenance, and durable memory links.
- Library is the single source of truth for live + durable assets and relationships.
- System is strictly admin-only and isolated from normal operator/agent use.
- Design system ensures governance never feels hidden.
- Integration-First: every module delivers backend + contracts + projection + binding + evidence.

---

## Primary Screens (6 distinct top-level views)

### 1. HQ — Central Command & Orchestration Layer
**Purpose:** Sovereign control, intelligence, and collaboration layer.  
**Signature characteristic:** AurelEU can embody multiple roles and orchestrate other agents under specific legislation.

#### AurelEU (Central Brain / Sovereign Agent)
- Role Engine (can act as Global Chat, IDE, Hub orchestrator, etc.)
- Legislation Injector & Dispatcher (deploys instances under country-specific laws and regulations, e.g. AurelCro, AurelGer, AurelPol, AurelEU-UK)
- Cross-Aurel Orchestrator
- **Submodules**
  - Role Switcher
  - Legislation Profiles
  - Deployment Manager
  - Agent Dispatch Console

#### Command (System-wide Operations Dashboard)
- Health, runtime statuses, agent workload, pending approvals, live decisions, risk surface, engine metrics
- **Submodules**
  - Runtime Monitor
  - Approval Queue
  - Workload Balancer
  - Alert Center

#### Intelligence (Advanced World Data & Intel Layer)
- Active web scraping (targeted + broad), page extraction, document intelligence, monitoring + action tooling
- **Submodules**
  - Scraper Studio
  - Knowledge Ingestion
  - Real-time Monitor
  - Intel Reports

#### Board (Multi-party Collaboration Space)
- Chatroom for AurelEU + other agents + human operator
- Debates, decisions, handoffs, live memory sharing
- **Submodules**
  - Debate Rooms
  - Decision Logs
  - Agent-to-Agent Channels
  - Operator Presence

#### Library (Live Integrated Memory & Asset Hub)
- Active files, agents, workflows, durable memory, relationships, provenance graph
- **Submodules**
  - Asset Graph
  - Memory Explorer
  - Workflow Library
  - Relationship Mapper
  - Version History

---

### 2. Corp — Enterprise / Organizational Operating Layer
**Purpose:** Business-grade creation, operation, and value realization of agent environments.

#### Agency
- Portfolio Map
- Business Environment (Wizard, Strategy, Identity, Permissions, Legal & Regulatory)
- **Submodules**
  - Environment Creator
  - Agent Portfolio
  - Identity Manager
  - Permission Matrix
  - Compliance Profiles

#### Operations
- Lifecycle, runtime, live tasks, workflows, KPIs, metrics, decisions, risks, evidence
- **Submodules**
  - Task Runtime
  - Workflow Orchestrator
  - KPI Dashboard
  - Risk Register
  - Evidence Vault

#### Financial
- Overall Aurel finances, cost attribution, budget governance, billing
- **Submodules**
  - Cost Attribution
  - Budget Governance
  - Billing Console
  - ROI Analyzer

#### Studio (Business-specific Tooling)
- Management, measurement, evolution, testing, simulation exclusively for business use cases
- **Submodules**
  - Business Simulator
  - Metric Evolution
  - Scenario Tester
  - Process Designer

#### R&D (Internal Research & Development)
- **Submodules**
  - Experiment Tracker
  - Hypothesis Board
  - Internal Lab Access
  - Knowledge Transfer

---

### 3. HUB — Tool, Skill & Automation Creation Layer
**Purpose:** Constantly evolving creative and automation workspace (advanced NotebookLM-style builder).

- Flow / Skill / Workflow / Loop / Habit creator
- Automation builder
- Media & Documentation studio (images, video, audio, docs)
- Advanced research & synthesis engine
- Skill & tool registry / marketplace (governed)
- **Submodules**
  - Flow Studio
  - Skill Forge
  - Media Generator
  - Automation Composer
  - Registry Browser

---

### 4. Lab — Full AI Research & Development Digital Lab
**Purpose:** High-power AI experimentation, model development, and rigorous testing.

- Model fine-tuning
- LoRA / adapter development
- Comprehensive testing suites (unit, integration, adversarial, governance)
- Experiment tracking, simulation environments, dataset management
- Full AI power tooling
- **Submodules**
  - Fine-Tune Console
  - LoRA Lab
  - Evaluation Harness
  - Dataset Manager
  - Simulation Sandbox

---

### 5. WorkOPS — Collaborative Operator Workspace
**Purpose:** Day-to-day human + agent collaboration (Aurel-native hybrid of Claude Cowork + Warp/Cursor).

#### General
- Conversation history, multi-agent chat, task tracking
- **Submodules**
  - History Browser
  - Task Manager

#### Code
- Hybrid environment (Warp + Cowork + Cursor style) with full Aurel governance overlay (trace, approvals, durable checkpoints, memory injection)
- **Submodules**
  - Code Workspace
  - Governance Overlay Panel

---

### 6. System — Admin-only Control Plane (Isolated)
**Purpose:** Platform-level administration. Never used for normal operational work.

- Models & Routing
- Archive, Data, Security
- Usage, Controls, Tests, Engine Metrics
- Runtime configuration, policy enforcement, identity & legislation management at platform level
- Deep audit and observability
- **Submodules**
  - Model Router
  - Security Center
  - Data Archive
  - Usage Analytics
  - Engine Diagnostics
  - Policy Console

---

## Cross-Cutting Rules & Integration

- **AurelEU is the only role-fluid dispatcher** that can inject legislation and orchestrate country-specific agents while carrying the core Aurel invariants.
- **Library** is the canonical durable view of memory, assets, workflows, and relationships (tightly integrated with P6 durable spine).
- Every submodule must surface:
  - Trace links
  - Governance status / approvals
  - Provenance
  - Durable memory / state references
- **Vertical Slice Requirement**: Every module and submodule must eventually deliver backend capability + versioned contracts + projection/read-model + Shell/CLI binding + trace/evidence binding.
- **Design System**: All governance surfaces follow the same interaction patterns (never hidden).
- **Business Value**: Corp surfaces expose measurable ROI, risk, and financial governance.
- **Intelligence**: HQ.Intelligence + HUB + Lab form the advanced data and model intelligence layer.
- **Durability**: Library, Command, Board, and AurelEU state are the primary consumers of the P6 durable memory and replay engine.

---

## Screen-to-Phase Mapping (High-Level)

- **P2 (Shell evolution)**: Primary implementation of the 6 screens and their module trees.
- **P6 (Durable Spine)**: Library, Command, Board, and AurelEU durable state become real.
- **P9 (Custos Enforcement)**: Real-time governance UI across all screens.
- **P15–P19**: Distributed/hybrid visibility in WorkOPS.Code, Lab, HQ.Command, Corp.Operations.
- **P22–P24**: HUB and Lab mature as independent governed tools.
- **P25 (v0.9)**: Full vertical realization of the complete IA.
- **P30 (v1.0)**: Production-grade, mature 6-screen platform with all submodules.

This document is the single source of truth for the Aurel product surface until superseded by a council-approved v1.1.