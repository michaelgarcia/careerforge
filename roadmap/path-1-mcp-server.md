# Path 1 — CareerForge as a Claude Desktop MCP Extension

## Status: Future / Post v1

This document captures the full specification for evolving CareerForge into a Claude Desktop
MCP extension. It is preserved here so it can be picked up in a future session with full
context, without having to rediscover the reasoning.

---

## Why This Path Is Interesting

CareerForge's current architecture relies on Claude Code's proprietary subagent system
(`.claude/agents/*.md` files). This makes the product tightly coupled to the Claude Code
CLI, which requires a terminal and some technical comfort. The MCP (Model Context Protocol)
path breaks this dependency.

MCP is Anthropic's open standard for giving LLMs access to external tools and data. Claude
Desktop — the native Mac/Windows app included with Claude Pro — is a full MCP client. Every
Claude Pro subscriber already has a polished, well-designed chat interface sitting on their
machine. If CareerForge is exposed as an MCP server, **Claude Desktop becomes the UI for
free, with zero custom UI code written**.

The deeper reason this path is compelling: MCP's **`sampling/createMessage`** capability
allows the MCP server to make LLM completion requests *back through* Claude Desktop, using
the user's Pro subscription. This means complex, multi-step agent work (resume generation,
interview prep, job scoring) can be done entirely within the user's Pro plan — **no
Anthropic API key required**. The existing `.claude/agents/*.md` system prompts are loaded
by the MCP server and passed as the system context for each sampling request. The agent
logic doesn't move — it stays in the same files.

This is also the most architecturally clean path. Claude Desktop is the interface, the
reasoning engine, and the orchestrator. The MCP server is just a thin I/O and execution
layer. Responsibility is clearly separated.

Finally, MCP is the direction Anthropic is investing in. Claude Desktop's MCP ecosystem is
growing rapidly. Building CareerForge as an MCP server positions it alongside tools like
filesystem servers, browser-use plugins, and database connectors — making it composable
with other MCP tools a user may already have configured.

---

## What This Path Is

### Architecture

```
User (Claude Desktop chat UI)
  │
  │  natural language request
  ▼
Claude Desktop (LLM brain + MCP client)
  │
  │  MCP tool calls
  ▼
CareerForge MCP Server (local Node.js or Python process)
  │                              │
  │  file I/O                   │  script execution
  ▼                              ▼
knowledge_base/              Python scripts (scanner)
config/                      Node.js scripts (docx gen)
output/
postings/
```

### Components to Build

**1. MCP Server** (`mcp-server/index.js` or `mcp_server.py`, ~300 LOC)

Exposes 10–12 tools to Claude Desktop:

| Tool | Description |
|------|-------------|
| `read_candidate_profile` | Returns structured KB data |
| `write_candidate_profile(data)` | Writes/updates candidate YAML |
| `list_source_files` | Lists files in knowledge_base/sources/ |
| `read_source_file(filename)` | Returns contents of a source file |
| `open_sources_folder` | Opens the sources folder in Explorer/Finder |
| `read_preferences` | Returns config/preferences.yaml |
| `write_preferences(data)` | Updates preferences config |
| `run_agent(agent_name, context)` | Loads agent .md, makes sampling request |
| `generate_docx(content, output_path)` | Calls generate_docx.js subprocess |
| `run_linkedin_scan(params)` | Runs Python scanner scripts |
| `list_job_postings` | Returns jobs from data/jobs.db |
| `update_tracker(posting_id, status)` | Updates postings/tracker.yaml |

The `run_agent` tool is the key one. It:
1. Reads `.claude/agents/{agent_name}.md` to extract the system prompt
2. Assembles the context messages (KB data, job description, etc.)
3. Makes a `sampling/createMessage` request to Claude Desktop
4. Claude Desktop runs the completion with its Pro subscription
5. Returns the result to the MCP server

This means **all 9 existing agent definitions are reused unchanged**. The agent system
prompt files don't need to be rewritten.

**2. System Prompt / Project Instructions for Claude Desktop**

A `mcp-server/careerforge_instructions.md` file that replicates the CLAUDE.md routing
logic for Claude Desktop. This is what Claude Desktop reads to understand:
- What CareerForge is
- When to call which tools
- How to sequence tools for multi-step workflows (e.g., apply = score + resume + cover letter)
- How to handle first-run onboarding

**3. Setup Wizard** (`setup/index.js`, ~100 LOC)

Run via `npx careerforge-setup`. Does:
1. Checks Node.js (≥18) and Python (≥3.11)
2. Installs Python deps (`pip install -r requirements.txt`)
3. Installs Node.js deps (`npm install` in mcp-server/)
4. Creates `~/careerforge/` data directory if needed
5. Auto-patches `~/Library/Application Support/Claude/claude_desktop_config.json`
   (Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
6. Prompts user to open Claude Desktop and say hello

Claude Desktop config snippet added by setup:
```json
{
  "mcpServers": {
    "careerforge": {
      "command": "node",
      "args": ["/path/to/careerforge/mcp-server/index.js"],
      "env": {}
    }
  }
}
```

**4. Packaging**

- `package.json` with `"bin": { "careerforge-setup": "./setup/index.js" }`
- Publishable to npm: `npm publish`
- Users: `npx careerforge-setup` (no global install needed)
- For truly non-technical users: a `Setup-CareerForge.bat` / `Setup-CareerForge.command`
  that calls `npx careerforge-setup` in a visible terminal window

---

## How the MCP Sampling Mechanism Works

This is the core technical question for this path. MCP's sampling API works as follows:

1. The MCP server calls `client.createMessage(request)` where `request` contains:
   - `systemPrompt`: the agent's system prompt (loaded from `.claude/agents/resume-writer.md`)
   - `messages`: the conversation messages (KB context + user request)
   - `maxTokens`: output token budget

2. Claude Desktop receives the sampling request and runs a completion using the user's
   Pro subscription

3. The completion result is returned to the MCP server, which then processes it
   (e.g., passes the resume markdown to `generate_docx.js`)

**Key consideration:** The sampling request competes with Claude Desktop's own context window.
CareerForge KB files can be 10–20k tokens. Before building, validate that:
- Claude Desktop supports sampling with large context
- The KB context can be chunked if needed (e.g., send only relevant sections)
- Latency is acceptable for the user experience

**Fallback:** If sampling has limitations, the MCP server can be extended to call the
Anthropic API directly for the heavy agent tasks, with an API key as an optional configuration.
This degrades gracefully: works with Pro subscription via sampling, works faster with API key.

---

## Tradeoffs vs. Path 2 (Enhanced Claude Code)

| Dimension | Path 1: MCP Server | Path 2: Enhanced Claude Code |
|-----------|-------------------|------------------------------|
| **Implementation effort** | ~2 days (MCP server + setup wizard) | Hours (CLAUDE.md edits only) |
| **Non-technical accessibility** | High — Claude Desktop is a polished native app | Medium — still requires terminal + Claude Code install |
| **Agent logic changes** | None (reused via sampling) | None |
| **Architecture cleanliness** | High — clear separation of concerns | Low — everything bundled in Claude Code |
| **Routing** | Implicit via Claude Desktop tool selection | Explicit via CLAUDE.md dispatcher rules |
| **Power user slash commands** | Still available in Claude Code as a parallel path | Full support, unchanged |
| **Future extensibility** | Easy — add MCP tools, compose with other MCP servers | Harder — CLAUDE.md can get large |
| **Background scanning** | Needs API key (runs without user in loop) | Needs API key (same constraint) |
| **Distribution** | npm package, one command | Git clone + Claude Code install |
| **Risk** | Sampling API must be tested; community unknown territory | Low risk — well-understood system |

**When to choose Path 1 over Path 2:**
- When non-technical accessibility is the primary goal (not just power-user convenience)
- When you want Claude Desktop as the primary interface (no terminal exposure)
- When you're ready to invest ~2 days of focused implementation
- When you want the system to be composable with other MCP tools

---

## Implementation Checklist (for future session)

- [ ] Verify Claude Desktop sampling API supports 15–20k token context
- [ ] Build MCP server skeleton with tool registration
- [ ] Implement `run_agent` tool (sampling + agent .md loading)
- [ ] Implement file I/O tools (read/write KB, list sources)
- [ ] Implement script execution tools (docx, scanner)
- [ ] Write `careerforge_instructions.md` (Claude Desktop system prompt)
- [ ] Build setup wizard (`npx careerforge-setup`)
- [ ] Test end-to-end: "generate a resume for [URL]" in Claude Desktop
- [ ] Write `Setup-CareerForge.bat` and `Setup-CareerForge.command` for non-technical users
- [ ] Publish to npm

---

## References

- MCP specification: https://spec.modelcontextprotocol.io
- Claude Desktop MCP setup guide: https://modelcontextprotocol.io/quickstart/user
- MCP sampling: https://spec.modelcontextprotocol.io/specification/client/sampling/
- Example MCP servers: https://github.com/modelcontextprotocol/servers
