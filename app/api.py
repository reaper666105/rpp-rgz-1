from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func, text

from .extensions import db
from .models import Item

api_bp = Blueprint("api", __name__)


def _json_error(message: str, *, status_code: int = 400, details: dict | None = None):
    payload: dict = {"error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


def _get_json_object():
    data = request.get_json(silent=True)
    if data is None:
        return None, _json_error("Request body must be valid JSON object.", status_code=400)
    if not isinstance(data, dict):
        return None, _json_error("JSON body must be an object.", status_code=400)
    return data, None


def _as_non_empty_str(value, field: str) -> tuple[str | None, tuple | None]:
    if not isinstance(value, str):
        return None, _json_error(f"Field '{field}' must be a string.", status_code=400)
    value = value.strip()
    if not value:
        return None, _json_error(f"Field '{field}' cannot be empty.", status_code=400)
    return value, None


def _as_int(value, field: str) -> tuple[int | None, tuple | None]:
    if isinstance(value, bool):
        return None, _json_error(f"Field '{field}' must be an integer.", status_code=400)
    if isinstance(value, int):
        return value, None
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value), None
    return None, _json_error(f"Field '{field}' must be an integer.", status_code=400)


def _as_decimal(value, field: str) -> tuple[Decimal | None, tuple | None]:
    if isinstance(value, bool):
        return None, _json_error(f"Field '{field}' must be a number.", status_code=400)
    if isinstance(value, (int, float, str)):
        try:
            dec = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None, _json_error(f"Field '{field}' must be a number.", status_code=400)
        return dec, None
    return None, _json_error(f"Field '{field}' must be a number.", status_code=400)


@api_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover
        return _json_error("Database is not reachable.", status_code=503, details={"reason": str(exc)})
    return jsonify({"status": "ok"})


@api_bp.post("/items")
def create_item():
    data, err = _get_json_object()
    if err:
        return err

    missing = [k for k in ("name", "quantity", "price", "category") if k not in data]
    if missing:
        return _json_error("Missing required fields.", details={"missing": missing})

    name, err = _as_non_empty_str(data.get("name"), "name")
    if err:
        return err

    category, err = _as_non_empty_str(data.get("category"), "category")
    if err:
        return err

    quantity, err = _as_int(data.get("quantity"), "quantity")
    if err:
        return err
    if quantity < 0:
        return _json_error("Field 'quantity' cannot be negative.", status_code=400)

    price, err = _as_decimal(data.get("price"), "price")
    if err:
        return err
    if price <= 0:
        return _json_error("Field 'price' must be greater than zero.", status_code=400)

    item = Item(name=name, quantity=quantity, price=price, category=category)
    db.session.add(item)
    db.session.commit()

    return jsonify(item.to_dict()), 201


@api_bp.get("/items")
def list_items():
    category = request.args.get("category")

    query = Item.query.order_by(Item.id.asc())
    if category:
        query = query.filter(Item.category == category)

    items = query.all()
    return jsonify([i.to_dict() for i in items])


@api_bp.get("/items/<int:item_id>")
def get_item(item_id: int):
    item = db.session.get(Item, item_id)
    if item is None:
        return _json_error("Item not found.", status_code=404)
    return jsonify(item.to_dict())


@api_bp.put("/items/<int:item_id>")
def update_item(item_id: int):
    item = db.session.get(Item, item_id)
    if item is None:
        return _json_error("Item not found.", status_code=404)

    data, err = _get_json_object()
    if err:
        return err

    allowed = {"name", "quantity", "price", "category"}
    unknown = sorted([k for k in data.keys() if k not in allowed])
    if unknown:
        return _json_error("Unknown fields in request body.", details={"unknown": unknown})

    if "name" in data:
        name, err = _as_non_empty_str(data.get("name"), "name")
        if err:
            return err
        item.name = name

    if "category" in data:
        category, err = _as_non_empty_str(data.get("category"), "category")
        if err:
            return err
        item.category = category

    if "quantity" in data:
        quantity, err = _as_int(data.get("quantity"), "quantity")
        if err:
            return err
        if quantity < 0:
            return _json_error("Field 'quantity' cannot be negative.", status_code=400)
        item.quantity = quantity

    if "price" in data:
        price, err = _as_decimal(data.get("price"), "price")
        if err:
            return err
        if price <= 0:
            return _json_error("Field 'price' must be greater than zero.", status_code=400)
        item.price = price

    db.session.commit()
    return jsonify(item.to_dict())


@api_bp.delete("/items/<int:item_id>")
def delete_item(item_id: int):
    item = db.session.get(Item, item_id)
    if item is None:
        return _json_error("Item not found.", status_code=404)

    db.session.delete(item)
    db.session.commit()
    return "", 204


def _build_summary_payload() -> dict:
    total_value = db.session.query(func.coalesce(func.sum(Item.quantity * Item.price), 0)).scalar()
    if total_value is None:
        total_value = Decimal("0")

    category_rows = (
        db.session.query(
            Item.category.label("category"),
            func.count(Item.id).label("items_count"),
            func.coalesce(func.sum(Item.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(Item.quantity * Item.price), 0).label("total_value"),
        )
        .group_by(Item.category)
        .order_by(Item.category.asc())
        .all()
    )

    categories = [
        {
            "category": r.category,
            "items_count": int(r.items_count),
            "total_quantity": int(r.total_quantity),
            "total_value": float(r.total_value),
        }
        for r in category_rows
    ]

    non_positive_items = Item.query.filter(Item.quantity <= 0).order_by(Item.id.asc()).all()

    return {
        "total_value": float(total_value),
        "categories": categories,
        "items_with_non_positive_quantity": [i.to_dict() for i in non_positive_items],
    }


def _summary_to_csv(summary: dict) -> str:
    buf = io.StringIO(newline="")
    w = csv.writer(buf)

    w.writerow(["total_value", summary["total_value"]])
    w.writerow(["non_positive_items_count", len(summary["items_with_non_positive_quantity"])])
    w.writerow([])

    w.writerow(["category", "items_count", "total_quantity", "total_value"])
    for c in summary["categories"]:
        w.writerow([c["category"], c["items_count"], c["total_quantity"], c["total_value"]])

    w.writerow([])
    w.writerow(["id", "name", "quantity", "price", "category"])
    for i in summary["items_with_non_positive_quantity"]:
        w.writerow([i["id"], i["name"], i["quantity"], i["price"], i["category"]])

    return buf.getvalue()


@api_bp.get("/reports/summary")
def report_summary():
    summary = _build_summary_payload()

    fmt = (request.args.get("format") or "json").lower()
    if fmt == "csv":
        csv_text = _summary_to_csv(summary)
        return Response(
            csv_text,
            status=200,
            mimetype="text/csv",
            headers={"Content-Disposition": "inline; filename=summary.csv"},
        )

    return jsonify(summary)

