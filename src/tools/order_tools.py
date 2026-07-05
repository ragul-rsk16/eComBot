import re


MOCK_ORDERS = {
    "ORD-001": {
        "order_id": "ORD-001",
        "status": "Shipped",
        "eta": "5 Jun 2026",
        "carrier": "BlueDart",
    },
    "ORD-002": {
        "order_id": "ORD-002",
        "status": "Processing",
        "eta": "7 Jun 2026",
        "carrier": "DTDC",
    },
    "ORD-003": {
        "order_id": "ORD-003",
        "status": "Delivered",
        "eta": "Already delivered",
        "carrier": "FedEx",
    },
}


def get_order_status(order_id: str, tool_context) -> dict:
    if not isinstance(order_id, str) or not re.fullmatch(r"ORD-\d{3}", order_id):
        return {"error": "Invalid order ID format."}

    if order_id not in MOCK_ORDERS:
        return {"error": f"Order {order_id} not found."}

    tool_context.state["last_order_id"] = order_id
    return MOCK_ORDERS[order_id]
