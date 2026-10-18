Hosting CrewAI multi-agent crew with Amazon Bedrock models in Amazon Bedrock AgentCore Runtime

Notes:
- The first two architecture images in the notebook seem to be missing from the images/ directory (also in original repo: https://github.com/awslabs/agentcore-samples/blob/main/06-workshops/01-AgentCore-runtime/01-hosting-agent/04-crewai-with-bedrock-model/images/

---

## Discussion: deployment interface and AgentCore Runtime V2 (status as of Oct 2026)

Context: evaluating this notebook as a course demo (AWS Agentic AI course) for running a
third-party agentic framework (CrewAI) on AgentCore. The notes below capture what we
established about the deployment interface it uses and its future direction.

### What the notebook uses to deploy

The "Configure AgentCore Runtime deployment" section uses the Python notebook wrapper
`Runtime()` from `bedrock-agentcore-starter-toolkit`:

```python
from bedrock_agentcore_starter_toolkit import Runtime
agentcore_runtime = Runtime()
agentcore_runtime.configure(entrypoint=..., auto_create_execution_role=True, auto_create_ecr=True, ...)
agentcore_runtime.launch()
agentcore_runtime.status()
```

The wrapper does three things: `configure` (generates Dockerfile + `.bedrock_agentcore.yaml`,
optionally auto-creates the IAM execution role and ECR repo), `launch` (builds the image,
pushes to ECR, calls the control-plane to create/update the runtime, polls the endpoint),
and `status`. Invocation already uses plain boto3 (`bedrock-agentcore` data-plane client,
`invoke_agent_runtime`), so that half is not toolkit-dependent.

### "No longer supported" — the precise scope

- The deprecation notice refers to the Starter Toolkit **CLI**, not the whole package.
- The named successor is the **AgentCore CLI** (`@aws/agentcore`), a Node.js tool
  (`npm install -g @aws/agentcore`, Node 20.x+). Authoritative repos:
  - Legacy toolkit (now labelled [LEGACY], links to a Migration Guide):
    https://github.com/aws/bedrock-agentcore-starter-toolkit
  - Successor CLI: https://github.com/aws/agentcore-cli
- There are two security advisories against the starter toolkit
  (CVE-2026-105812 / CVE-2026-106032).

### Does the successor expose a Python module?

No. `@aws/agentcore` is a Node/TypeScript terminal tool (`agentcore create / dev / deploy /
invoke`, config via `agentcore.json`, generated CDK). There is no importable Python
equivalent to `from bedrock_agentcore_starter_toolkit import Runtime`. In a notebook it
would be driven through shell cells, not a Python object.

Framework note: the CLI's first-class frameworks are Strands, LangChain/LangGraph,
Google ADK, OpenAI Agents, and Bedrock Managed Agents. **CrewAI is not first-class** there —
it would go through the generic BYO/container path. This is why, for a CrewAI demo, the
legacy Python toolkit is actually the cleaner story right now.

### Is there a Python successor to the `Runtime()` wrapper?

No direct drop-in Python successor exists. The strategic replacement is the Node CLI. The
legacy Python toolkit still installs and runs (confirmed by `uv sync` in the notebook:
`bedrock-agentcore-starter-toolkit==0.1.1`, `bedrock-agentcore==1.24.1`), but it is frozen
as legacy.

### AgentCore Runtime V2

- V2 shipped Sep 2026 (GA announcement:
  https://aws.amazon.com/about-aws/whats-new/2026/09/new-agentcore-runtime-generally-available/).
  Benefits: elastic memory, consistent/faster cold starts (snapshot restore).
- Opt-in via a single parameter: **set `platformVersion` to `V2`** on the control-plane
  `create_agent_runtime` / `update_agent_runtime` call.
- Available regions at launch: us-east-1, us-east-2, us-west-2, eu-west-1, ap-northeast-1.

**Does the `Runtime()` wrapper expose V2?** The installed `0.1.1` wrapper's `configure()`
signature (`entrypoint`, `execution_role`, `agent_name`, `requirements`,
`requirements_file`, `ecr_repository`, `container_runtime`, `auto_create_ecr`,
`auto_create_execution_role`, `authorizer_configuration`, `region`, `protocol`) and
`launch()` have **no `platform_version` passthrough** — so deployments default to V1. A
deeper grep to prove V2 is entirely absent from the package was not completed, so treat
"wrapper cannot do V2" as very likely rather than fully confirmed. If V2 is needed later,
the lightest path is a small boto3 helper around `create/update_agent_runtime` with
`platformVersion="V2"` rather than relying on the wrapper.

### Decision

Keep this notebook as-is as a candidate demo for showing AgentCore running a CrewAI
multi-agent crew. The legacy Python toolkit is a valid, readable fit for the CrewAI story
today. Direct-boto3 deployment and/or V2 are future options if the demo needs them.
