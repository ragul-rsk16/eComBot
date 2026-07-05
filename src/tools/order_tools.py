import re

'''
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
'''

import logging
from typing import Any
from google.adk.tools import ToolContext

try:
    from .db import execute, query_all, query_one
except ImportError:  # pragma: no cover
    from db import execute, query_all, query_one

log = logging.getLogger(__name__)

def get_order_status(order_id: str, tool_context) -> dict:
    if not isinstance(order_id, str) or not re.fullmatch(r"ORD-\d{3}", order_id):
        return {"found": False, "error": "Invalid order ID format."}

    try:
        row = query_one("SELECT * FROM orders WHERE order_id = %s", (order_id,))
    except Exception as exc:
        log.error("DB error in get_order_status: %s", exc)
        return {"found": False, "error": "Order lookup is temporarily unavailable. Please try again shortly."}

    if row is None:
        return {
            "found": False,
            "order_id": order_id,
            "error": f"No order found for '{order_id}'. Please check the reference and try again.",
        }

    # Persist the order context for this session turn
    tool_context.state["current_order_id"] = order_id

    return {
        "found": True,
        "order_id": row["order_id"],
        "carrier": row["carrier"],
        "eta": str(row["eta"]),
        "status": row["status"],
    }
