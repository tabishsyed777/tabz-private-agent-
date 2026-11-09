import ollama
import json
import subprocess
import sys
from pathlib import Path

MODEL = "qwen2.5-coder:7b"
WORKSPACE = Path(__file__).resolve().parent

# ---------- Tools the manager can use ----------

def write_file(path: str, content: str) -> str:
    target = _workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w") as f:
        f.write(content)
    return f"Wrote {target.relative_to(WORKSPACE)}"

def read_file(path: str) -> str:
    try:
        with _workspace_path(path).open() as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: {path} does not exist"


def _workspace_path(path: str) -> Path:
    """Keep model-requested file access inside this project directory."""
    target = (WORKSPACE / path).resolve()
    if not target.is_relative_to(WORKSPACE):
        raise ValueError("Only paths inside the project workspace are allowed.")
    return target

def run_tests() -> str:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
    )
    return (result.stdout + result.stderr)[-2000:]

# ---------- Helper to describe a tool to the model ----------

def tool(name, description, params):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": list(params.keys()),
            },
        },
    }

# ---------- The agent loop ----------

class Agent:
    def __init__(self, name, role, tools, handlers):
        self.name = name
        self.role = role
        self.tools = tools
        self.handlers = handlers

    def _text_tool_call(self, text):
        """Accept qwen's JSON fallback when it declines native tool calling."""
        try:
            candidate = text.strip().removeprefix("```json").strip()
            start = candidate.index("{")
            call, _ = json.JSONDecoder().raw_decode(candidate[start:])
        except (json.JSONDecodeError, ValueError):
            return None
        name, args = call.get("name"), call.get("arguments")
        if name in self.handlers and isinstance(args, dict):
            return {"function": {"name": name, "arguments": args}}
        return None

    def run(self, task, max_steps=12):
        # A fresh history prevents one completed job from contaminating the next.
        messages = [
            {"role": "system", "content": self.role},
            {"role": "user", "content": task},
        ]
        for _ in range(max_steps):
            response = ollama.chat(model=MODEL, messages=messages, tools=self.tools)
            msg = response["message"]
            content = msg.get("content", "")
            native_calls = msg.get("tool_calls") or []
            calls = native_calls or ([self._text_tool_call(content)] if content else [])
            calls = [call for call in calls if call]
            messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": native_calls or None,
            })

            # No tool calls means the agent is finished and this is its answer
            if not calls:
                return content

            # Otherwise run each requested tool and feed the result back
            for call in calls:
                name = call["function"]["name"]
                args = call["function"]["arguments"]
                print(f"[{self.name}] calls {name}({args})")
                try:
                    result = self.handlers[name](**args)
                except Exception as exc:
                    result = f"Tool error: {exc}"
                # Delegation is a one-shot handoff.  Small local models often keep
                # delegating after they have already received a complete report.
                if name.startswith("delegate_to_"):
                    return str(result)
                # User-role feedback also works with models that emitted JSON rather
                # than Ollama's native tool-call structure.
                messages.append({
                    "role": "user",
                    "content": f"Tool result from {name}:\n{result}\nContinue the task.",
                })

        return "Stopped: step limit reached."

# ---------- Build the hierarchy (bottom up) ----------

manager = Agent(
    name="manager",
    role=(
        "You are a manager. Do the task you are given using your tools: "
        "write_file to create code, read_file to check it, and run_tests to verify. "
        "For a request to create files, write the requested files before running tests. "
        "Do not run tests as your first action when the requested files do not exist. "
        "When finished, reply with a short summary of what you did."
    ),
    tools=[
        tool("write_file", "Write text to a file.",
             {"path": {"type": "string"}, "content": {"type": "string"}}),
        tool("read_file", "Read a file.",
             {"path": {"type": "string"}}),
        tool("run_tests", "Run the pytest test suite.", {}),
    ],
    handlers={"write_file": write_file, "read_file": read_file, "run_tests": run_tests},
)

director = Agent(
    name="director",
    role=(
        "You are a director. Turn the goal you receive into one clear, concrete task "
        "and send it to the manager with delegate_to_manager. "
        "When the manager reports back, summarize the result in one paragraph."
    ),
    tools=[
        tool("delegate_to_manager", "Send a concrete task to the manager.",
             {"task": {"type": "string"}}),
    ],
    handlers={"delegate_to_manager": lambda task: manager.run(task)},
)

ceo = Agent(
    name="ceo",
    role=(
        "You are the CEO. Do not write code yourself. Send the user's goal to the "
        "director with delegate_to_director. When the director reports back, "
        "give the user a short final status."
    ),
    tools=[
        tool("delegate_to_director", "Send a goal to the director.",
             {"goal": {"type": "string"}}),
    ],
    handlers={"delegate_to_director": lambda goal: director.run(goal)},
)

# ---------- Run it ----------

if __name__ == "__main__":
    goal = input("What should the company build? ")
    print("\nFinal status:\n", ceo.run(goal))
