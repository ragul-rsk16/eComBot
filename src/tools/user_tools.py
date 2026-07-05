def save_user_name(name: str, tool_context) -> str:
    tool_context.state["user_name"] = name
    return f"Nice to meet you, {name}!"

def build_greeting(tool_context) -> str:
    name = tool_context.state.get("user_name")
    last_order = tool_context.state.get("last_order_id")

    greeting = "Hello!"

    if name:
        greeting = f"Hello {name}!"

    if last_order:
        greeting += f" I see your last order is {last_order}."

    return greeting + " How can I help you today?"