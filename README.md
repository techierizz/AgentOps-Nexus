# AgentOps Nexus

### Autonomous Self-Learning Multi-Agent Bug Resolution Platform

AgentOps Nexus is an autonomous software engineering agent system that parses incoming repository issue tickets, builds static codebase AST knowledge graphs, generates and ranks bug hypotheses, validates the root cause, and applies secure patches iteratively inside an automated verification loop.

---

## 🌌 Core Vision & Unique Innovation

Most autonomous coding systems are simple wrappers around LLMs that try to edit code directly through copy-pasting code blocks. AgentOps Nexus introduces three research-inspired components that elevate it to a production-grade self-healing system:

1. **Bug Hypothesis Generation & Ranking**: Mirrors the cognitive process of human senior engineers. Rather than patching symptoms, the system generates multiple hypotheses, scores them based on AST trace analysis, and validates them statically against the codebase before code edits are allowed.
2. **Software AST Knowledge Graph**: Built locally using `NetworkX`. It indexes files, classes, methods, imports, and call hierarchies to evaluate the semantic impact of proposed changes.
3. **Retrieval-Augmented Agent Memory**: Stores historical issue signatures and patches in a vectorized memory engine. Similar bugs retrieved guide future fixes, facilitating continuous learning.

---

## 🛠️ Architecture & Multi-Agent Loop

```
  [User Issue Submitted]
           │
           ▼
     [Issue Agent] (Extracts stack traces, targets, and symbols)
           │
           ▼
    [Repo Intel Agent] (Builds AST Knowledge Graph using NetworkX)
           │
           ▼
     [Memory Agent] (Retrieves historical fixes from local FAISS/Vector memory)
           │
           ▼
   [Hypothesis Agent] (Formulates and ranks potential bug hypotheses)
           │
           ▼
      [RCA Agent] (Performs static Root Cause Validation against code files)
           │
           ▼
  ┌──► [Patch Agent] (Applies modifications, outputs unified diffs)
  │        │
  │        ▼
  │  [Security Agent] (Scans diff for secrets, eval, and injection risks)
  │        │
  │        ▼
  │  [Testing Agent] (Launches pytest subprocess, evaluates results)
  │        │
  │        ▼
  └── [Reflection Agent] (On failure, analyzes pytest stack logs and corrects patch)
           │
     (On Success)
           │
           ▼
   [Confidence Agent] (Computes 0-100 score, Risk Level, and Merge Safety)
           │
           ▼
      [PR Agent] (Commits code, switches branch, and registers PR template)
```

---

## 📂 Folder Structure

```
d:\Japan\
├── README.md                           # Master documentation
├── docker-compose.yml                  # Multi-container orchestration
├── backend.Dockerfile                  # FastAPI container setup
├── frontend.Dockerfile                 # React + Nginx container setup
├── requirements.txt                    # Python dependency manifest
├── package.json                        # Root npm configuration
│
├── backend/                            # FastAPI Server & Agents
│   ├── main.py                         # API endpoints and SSE stream routers
│   ├── config.py                       # Global environments and paths config
│   ├── orchestrator.py                 # Multi-agent state machine runner
│   ├── database.py                     # Demo issues database and target reset utility
│   │
│   ├── agents/                         # Agent Implementations
│   │   ├── base.py                     # Agent State TypedDict and BaseAgent
│   │   ├── issue_agent.py              # Extract issue meta and traces
│   │   ├── repo_agent.py               # AST codebase indexing
│   │   ├── memory_agent.py             # Vector lookup helper
│   │   ├── hypothesis_agent.py         # Formulate and rank bug hypotheses
│   │   ├── rca_agent.py                # Validate root cause candidates
│   │   ├── patch_agent.py              # Code patching engine
│   │   ├── security_agent.py           # Vulnerability scanner
│   │   ├── testing_agent.py            # Subprocess test launcher
│   │   ├── reflection_agent.py         # Self-correction logic generator
│   │   ├── confidence_agent.py         # Multi-factor confidence score
│   │   └── pr_agent.py                 # Git committer and PR issuer
│   │
│   └── utils/
│       ├── ast_parser.py               # AST code parser
│       ├── vector_store.py             # Pure-python TF-IDF cosine similarity store
│       └── git_client.py               # Git subprocess wrapper
│
├── frontend/                           # React + Vite Client
│   ├── src/
│   │   ├── main.tsx                    # React mounting entrypoint
│   │   ├── App.tsx                     # SSE listener and main dashboard
│   │   ├── index.css                   # Custom scrollbars, glows, and animations
│   │   ├── types.ts                    # TypeScript interface contracts
│   │   └── components/
│   │       ├── Header.tsx              # Trigger controls
│   │       ├── IssueQueue.tsx          # Selection list
│   │       ├── LiveConsole.tsx         # Agent workflow progress & logs
│   │       ├── GraphView.tsx           # Custom interactive SVG Graph layout
│   │       ├── MemoryCenter.tsx        # Vector matches panel
│   │       ├── ConfidenceCenter.tsx    # Safety gauge and decision weight sliders
│   │       └── PRCenter.tsx            # Unified diff and branch status
│   │
│   └── postcss.config.js               # PostCSS compilation rules (Tailwind v4)
│
└── demo_target_repo/                   # Target repository containing the bugs
    ├── payment_processor.py            # Code file with ZeroDivision, Import, and TypeError bugs
    ├── stripe_client.py                # Stripe mock helper
    └── test_payment.py                 # Pytest suite
```

---

## 🛢️ Database & Graph Schema

### 1. Vector Memory Document Schema
Historical fixes are indexed using the following JSON model:
```json
{
  "id": "MEM-NEXUS-101",
  "content": "[Issue Title]: [Issue Description]",
  "metadata": {
    "issue_title": "ZeroDivisionError in calculate_fees()",
    "root_cause": "Division by zero where payment fees are calculated by dividing total transaction fees by total_items without validation.",
    "patch_summary": "Add safety check: if total_items == 0, set fee_per_item = 0.",
    "files_changed": ["payment_processor.py"],
    "confidence_score": 96
  }
}
```

### 2. Software Knowledge Graph Schema (NetworkX)
* **Nodes**:
  * `File`: `{"id": "payment_processor.py", "type": "file", "properties": {"size": 1840}}`
  * `Class`: `{"id": "payment_processor.py::PaymentProcessor", "type": "class", "properties": {"bases": []}}`
  * `Function`: `{"id": "payment_processor.py::PaymentProcessor::calculate_fees", "type": "function", "properties": {"args": ["total_fee", "total_items"]}}`
* **Edges**:
  * `declared_in`: `Class` or `Function` -> `File`
  * `calls`: `Function A` -> `Function B` (representing function calls inside bodies)
  * `imports`: `File A` -> `File B` (cross-module dynamic or static imports)

---

## 🔌 API Definitions

### `GET /api/issues`
Returns list of demo issues.

### `POST /api/run-agent`
Spawns background orchestrator thread for target issue.
* **Body**: `{"issue_id": "NEXUS-101"}`
* **Response**: `{"status": "success", "run_id": "NEXUS-101"}`

### `GET /api/stream/{run_id}`
Server-Sent Events (SSE) stream returning JSON text snapshots of `AgentState` on state transitions.

### `POST /api/reset-demo`
Restores all target files in `demo_target_repo` to their initial buggy state and cleans up git history.

---

## 🚀 Local Execution & Development

### 1. Backend Server Setup
Ensure Python 3.12+ is installed, then run:
```bash
# Install dependencies
pip install -r requirements.txt

# Launch the Uvicorn dev server on port 8000
python backend/main.py
```

### 2. Frontend Client Setup
Ensure Node.js v22+ is installed, then run:
```bash
cd frontend
# Install packages
npm install

# Launch Vite local dev server on port 5173
npm run dev
```
Open `http://localhost:5173` to view the AgentOps Nexus Dashboard.

### 3. Docker Compose Deployment
To deploy both services inside a virtualized network environment:
```bash
docker-compose up --build
```
Open `http://localhost` to view the containerized dashboard.

---

## 🎬 Live Hackathon Demo Script (Under 2 Minutes!)

This script is designed to guarantee a flawless, high-impact presentation for judges.

1. **Preparation**:
   * Open the dashboard at `http://localhost:5173`.
   * Click **RESET DEMO REPO** in the header. This ensures the target repo is in its buggy state and the terminal log is empty.
2. **Step 1: Inspect the Issue** (0:00 - 0:15):
   * Select **NEXUS-101: ZeroDivisionError in calculate_fees()** from the Issue Queue. Show the stack trace. Explain that checking out free or promotional products (where total items equal 0) crashes the checkout process.
3. **Step 2: Deploy the Agents** (0:15 - 1:00):
   * Click **DEPLOY AGENTS**.
   * Point out the **AGENT PIPELINE** card layout. Explain how each agent is triggered sequentially.
   * Watch the **LIVE THINKING ENGINE** stream thought logs.
   * Highlight the **MEMORY ENGINE** panel showing retrieved similar historical bugs.
4. **Step 3: Root Cause Isolation & Knowledge Graph** (1:00 - 1:30):
   * Scroll to the **SOFTWARE KNOWLEDGE GRAPH**. Show how `payment_processor.py` nodes are generated.
   * Note how the `calculate_fees` function node turns **pulsating red** with radar indicator circles, validating the hypothesis!
5. **Step 4: Verification & Git Commit** (1:30 - 2:00):
   * Show the **CONFIDENCE & SAFETY** panel. Note that all 4 unit tests are passing (100% success) and the confidence score is calculated at **96%**.
   * Review the **PULL REQUEST CENTER** at the bottom, showcasing the color-coded code diff (green lines added, red lines removed) and the local git commit details.
   * Verify on your local file explorer that `demo_target_repo/payment_processor.py` has been patched.

---

## 🎤 Pitch Deck Slide Outline

* **Slide 1: Title & Tagline**
  * *AgentOps Nexus*: Autonomous Self-Learning Multi-Agent platform. The future of self-healing software codebases.
* **Slide 2: The Problem**
  * Current AI coding tools write patches without verifying if they work, lack context of call hierarchies, fail to learn from historical context, and introduce security vulnerabilities (e.g. leaking API keys).
* **Slide 3: The Solution**
  * Nexus's 11-agent pipeline. It does not just output code; it reasons (Hypotheses), checks calls (Knowledge Graph), retrieves context (Memory), scans vulnerabilities (Security), and runs local tests (Testing).
* **Slide 4: Key Innovation**
  * *Hypothesis-Driven Debugging*: Simulating Senior Engineers. Rather than guessing, the agent formulates, ranks, and validates multiple bug hypotheses before changing a single line of code.
* **Slide 5: Live Demo**
  * Demonstration of resolving a critical checkout ZeroDivisionError, validating tests, and compiling a PR in under 2 minutes.
* **Slide 6: Impact & Venture Potential**
  * Reduces software maintenance engineering overheads, prevents runtime server crashes automatically, and creates a repository-wide memory brain that makes teams smarter over time.

---

## 🗺️ Future Research Roadmap

1. **Predictive Bug Detection**: Run static analysis checks on commits to predict structural vulnerabilities before issues are even submitted.
2. **Cross-Repository Memory Learning**: Share learned vector memory templates across organization repositories so that a bug fixed in repository A immediately aids in fixing related bugs in repository B.
3. **Architecture Drift Detection**: Analyze knowledge graphs over time. Flag if developers are bypassing class structures, violating modular boundaries, or creating circular call graphs.
