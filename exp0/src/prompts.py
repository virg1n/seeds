from __future__ import annotations

import re

FENCE = "```"


def problem_prompt(task: dict) -> str:
    if task["source"] == "mbpp":
        return (f"{task['text']}\n\nWrite a Python function named `{task['entry']}`. "
                f"It must pass tests like:\n{task['example_test']}\n\n"
                f"Return only the code in a single {FENCE}python block.")
    if task["kind"] == "func":
        starter = task.get("starter") or ""
        return (f"Solve the following programming problem in Python 3.\n\n{task['text']}\n\n"
                f"Implement the function `{task['entry']}`" + (f" starting from:\n{FENCE}python\n{starter}\n{FENCE}\n"
                                                               if starter.strip() else ".\n") +
                f"\nReturn only the code in a single {FENCE}python block.")
    return (f"Solve the following programming problem in Python 3. Read the input from standard input "
            f"and print the answer to standard output.\n\n{task['text']}\n\n"
            f"Return only the code in a single {FENCE}python block.")


def plain(task):
    return [{"role": "user", "content": problem_prompt(task)}]


def strategy(task, s):
    return [{"role": "user", "content": f"Strategy {s}.\n\n" + problem_prompt(task)}]


def differently(task, previous_codes, max_lines=60):
    parts = [problem_prompt(task).rsplit("\n\nReturn only", 1)[0], "", "Here are previous solutions to this problem:"]
    for i, c in enumerate(previous_codes, 1):
        lines = c.strip().splitlines()
        if len(lines) > max_lines:
            lines = lines[:max_lines] + ["# ..."]
        parts.append(f"\nSolution {i}:\n{FENCE}python\n" + "\n".join(lines) + f"\n{FENCE}")
    parts.append("\nWrite a new correct solution that uses a genuinely different algorithm or approach than every "
                 "solution above (not just renamed variables or restyled code). "
                 f"Return only the code in a single {FENCE}python block.")
    return [{"role": "user", "content": "\n".join(parts)}]


_THINK = re.compile(r"<think>.*?</think>", re.S)
_BLOCK = re.compile(r"```[ \t]*(?:python3?|py)?[ \t]*\n(.*?)```", re.S | re.I)


def extract_code(text: str) -> str:
    text = _THINK.sub("", text or "")
    if "<think>" in text:  # unterminated thinking
        text = text.split("</think>")[-1]
    blocks = _BLOCK.findall(text)
    if blocks:
        return max(blocks, key=len).strip("\n") + "\n"
    m = re.search(r"```[ \t]*(?:python3?|py)?[ \t]*\n(.*)", text, re.S | re.I)  # unterminated fence
    if m:
        return m.group(1).strip("\n") + "\n"
    return text.strip() + "\n"
