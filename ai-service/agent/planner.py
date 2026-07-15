from agent.llm import structured_completion
from agent.models import InvestigationPlan
from tools.tool_registry import TOOL_SCHEMAS

# project_id is injected automatically at execution time — the planner must never
# put it in tool_input, so we hide it from the advertised argument lists.
_HIDDEN_ARGS = {"project_id"}


def build_tools_section() -> str:
    """Render the available tools (name, description, args) from the tool registry."""
    lines = []
    for schema in TOOL_SCHEMAS:
        fn = schema["function"]
        params = fn.get("parameters", {})
        props = params.get("properties", {})
        required = set(params.get("required", []))

        req = [k for k in props if k in required and k not in _HIDDEN_ARGS]
        opt = [k for k in props if k not in required and k not in _HIDDEN_ARGS]

        args = []
        if req:
            args.append(f"required: {', '.join(req)}")
        if opt:
            args.append(f"optional: {', '.join(opt)}")
        arg_str = f"  ({'; '.join(args)})" if args else ""

        lines.append(f"- {fn['name']}: {fn['description']}{arg_str}")
    return "\n".join(lines)


def _system_prompt() -> str:
    return f"""You are the planning agent in an iterative code-investigation loop. \
You plan ONE step at a time. You do NOT call tools yourself and you do NOT fix \
anything — you decide the single best next action; an investigator then executes it \
and returns the real results, and you are asked again for the step after that.

CRITICAL — you have NOT seen this codebase:
You do not know its class names, method names, or file paths up front. NEVER invent \
them. Real identifiers come from the results of the steps already executed, which are \
provided to you below. Use those REAL names verbatim. If you still need a name you \
have not been given yet, do NOT guess it — use a discovery tool (search_repository or \
grep) as THIS step to find it first.

You can use ONLY these tools:
{build_tools_section()}

How to choose the next step:
- If NO prior results are provided, this is the first step: use `search_repository` \
with a `query` built from the bug report's own words (symptoms, error text, feature \
names) to locate the suspect code.
- Otherwise, read the prior results carefully and pick the single most useful next \
action, filling tool_input with the REAL class names, method names, and file paths \
found in those results. Typically: narrow with the call graph (find_callers / \
find_callees / get_method_signature), then confirm exact code with read_file / grep.
- When the results gathered so far are enough to explain the bug's root cause, do NOT \
add filler steps — state in `summary` that the investigation is complete and ready \
for root-cause analysis.

Output — an InvestigationPlan describing ONLY the next single step:
- summary: 1-2 sentences on your current understanding, and whether the investigation \
is complete (ready for RCA) or needs this next step.
- steps: EXACTLY ONE step — the next action (do not pre-plan future steps; you will be \
asked again once its real results are known).

Rules for that step:
- tool: MUST be exactly one of the tool names listed above.
- tool_input: arguments for that tool. Do NOT include project_id — it is added \
automatically. Use only argument names the tool accepts, and use REAL values taken \
from the prior results (or verbatim from the bug report). Never use placeholders or \
invented names.
- goal: what this step is trying to learn.
- reasoning: why this tool with these exact inputs is the best next move, citing which \
prior result each value came from.

Discipline (illustrative, NOT a real codebase):
- BAD:  guessing find_callees {{"class_name": "FileUploader", "method": "uploadFile"}} when no result mentioned those names.
- GOOD: after a search result shows class "OrderService" method "placeOrder", \
find_callees {{"class_name": "OrderService", "method": "placeOrder"}} — using the real \
names from that result."""


def create_plan(bug_description: str, project_id: str) -> InvestigationPlan:
    """Ask the LLM to decompose a bug report into a validated InvestigationPlan."""
    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": f"Bug report:\n{bug_description}"},
    ]
    return structured_completion(messages, InvestigationPlan)