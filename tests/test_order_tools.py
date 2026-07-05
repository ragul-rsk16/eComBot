from src.tools.order_tools import get_order_status

def test_get_order_status_returns_mock_data_for_known_order():
    result = get_order_status("ORD-001")

    assert result["order_id"] == "ORD-001"
    assert result["status"] == "Shipped"
    assert result["eta"] == "5 Jun 2026"
    assert result["carrier"] == "BlueDart"


def test_get_order_status_returns_invalid_format_error():
    result = get_order_status("invalid")

    assert result == {"error": "Invalid order ID format."}


def test_get_order_status_returns_missing_order_error():
    result = get_order_status("ORD-999")

    assert result == {"error": "Order ORD-999 not found."}
