#!/usr/bin/env python3
import os
import json
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("splitwise")
BASE_URL = "https://secure.splitwise.com/api/v3.0"


def _headers():
    return {"Authorization": f"Bearer {os.environ['SPLITWISE_API_KEY']}"}


def _iso_date(date_str: str) -> str:
    """Normalize any date input to noon UTC to avoid timezone day-flip in the Splitwise app."""
    if not date_str:
        return date_str
    # Strip any existing time component and re-attach noon UTC
    day = date_str[:10]  # take YYYY-MM-DD portion
    return f"{day}T12:00:00Z"


@mcp.tool()
def list_groups() -> str:
    """List all Splitwise groups you belong to, with their IDs and names."""
    r = httpx.get(f"{BASE_URL}/get_groups", headers=_headers())
    r.raise_for_status()
    groups = r.json()["groups"]
    return json.dumps(
        [{"id": g["id"], "name": g["name"]} for g in groups], indent=2
    )


@mcp.tool()
def list_group_members(group_id: int) -> str:
    """List members of a Splitwise group with their user IDs and names."""
    r = httpx.get(f"{BASE_URL}/get_group/{group_id}", headers=_headers())
    r.raise_for_status()
    members = r.json()["group"]["members"]
    return json.dumps(
        [{"id": m["id"], "name": f"{m['first_name']} {m['last_name']}"} for m in members],
        indent=2,
    )


@mcp.tool()
def create_expense(
    description: str,
    cost: str,
    group_id: int,
    paid_by_user_id: int,
    splits: list,
    date: str = None,
    notes: str = None,
) -> str:
    """
    Create a Splitwise expense in a group with per-user splits.

    splits: list of {"user_id": int, "owed_share": str}
    All owed_share values must sum to cost.
    The paid_by_user_id is the person who paid the full amount.
    date: ISO 8601 format e.g. "2026-04-27T00:00:00Z" (optional)
    notes: extra details shown in the expense notes field (optional)

    Example:
      create_expense("Trader Joe's - Eggs", "8.97", 73654273, 94211279,
        [{"user_id": 94211279, "owed_share": "2.99"},
         {"user_id": 24465843, "owed_share": "2.99"},
         {"user_id": 29221111, "owed_share": "2.99"}],
        date="2026-04-27T00:00:00Z",
        notes="Eggs for the week")
    """
    data = {
        "cost": cost,
        "description": description,
        "group_id": group_id,
        "currency_code": "USD",
    }
    if date:
        data["date"] = _iso_date(date)
    if notes:
        data["details"] = notes

    for i, split in enumerate(splits):
        data[f"users__{i}__user_id"] = split["user_id"]
        data[f"users__{i}__owed_share"] = split["owed_share"]
        data[f"users__{i}__paid_share"] = cost if split["user_id"] == paid_by_user_id else "0.00"

    r = httpx.post(f"{BASE_URL}/create_expense", headers=_headers(), data=data)
    r.raise_for_status()
    result = r.json()

    if result.get("errors") and any(result["errors"].values()):
        return json.dumps({"error": result["errors"]})

    expense = result["expenses"][0]
    return json.dumps({
        "id": expense["id"],
        "description": expense["description"],
        "cost": expense["cost"],
        "group_id": expense["group_id"],
        "date": expense["date"],
        "notes": expense.get("details", ""),
    })


@mcp.tool()
def update_expense(
    expense_id: int,
    description: str = None,
    cost: str = None,
    date: str = None,
    notes: str = None,
    group_id: int = None,
    paid_by_user_id: int = None,
    splits: list = None,
) -> str:
    """
    Update an existing Splitwise expense.

    expense_id: ID of the expense to update
    description: new description (optional)
    cost: new cost as string e.g. "12.50" (optional)
    date: ISO 8601 date e.g. "2026-04-27T00:00:00Z" (optional)
    notes: text for the notes/details field (optional)
    group_id: group to move expense to (optional)
    paid_by_user_id: user who paid (required if updating splits)
    splits: list of {"user_id": int, "owed_share": str} (optional)

    Example:
      update_expense(12345678, date="2026-04-27T00:00:00Z", notes="Dinner at Niagara")
    """
    data = {}
    if description:
        data["description"] = description
    if cost:
        data["cost"] = cost
        data["currency_code"] = "USD"
    if date:
        data["date"] = _iso_date(date)
    if notes:
        data["details"] = notes
    if group_id:
        data["group_id"] = group_id
    if splits and paid_by_user_id and cost:
        for i, split in enumerate(splits):
            data[f"users__{i}__user_id"] = split["user_id"]
            data[f"users__{i}__owed_share"] = split["owed_share"]
            data[f"users__{i}__paid_share"] = cost if split["user_id"] == paid_by_user_id else "0.00"

    r = httpx.post(f"{BASE_URL}/update_expense/{expense_id}", headers=_headers(), data=data)
    r.raise_for_status()
    result = r.json()

    if result.get("errors") and any(result["errors"].values()):
        return json.dumps({"error": result["errors"]})

    expense = result["expenses"][0]
    return json.dumps({
        "id": expense["id"],
        "description": expense["description"],
        "cost": expense["cost"],
        "date": expense["date"],
        "notes": expense.get("details", ""),
    })


@mcp.tool()
def create_group(
    name: str,
    group_type: str = "other",
    members: list = None,
) -> str:
    """
    Create a new Splitwise group and optionally add members.

    name: display name for the group
    group_type: one of "apartment", "house", "trip", "other" (default "other")
    members: list of {"user_id": int} to add (optional - you are added automatically)

    Example:
      create_group("Road Trip 2026", group_type="trip",
        members=[{"user_id": 24465843}])
    """
    data = {"name": name, "group_type": group_type}
    if members:
        for i, m in enumerate(members):
            data[f"users__{i}__user_id"] = m["user_id"]

    r = httpx.post(f"{BASE_URL}/create_group", headers=_headers(), data=data)
    r.raise_for_status()
    result = r.json()

    if result.get("errors") and any(result["errors"].values()):
        return json.dumps({"error": result["errors"]})

    g = result["group"]
    return json.dumps({
        "id": g["id"],
        "name": g["name"],
        "group_type": g["group_type"],
        "members": [{"id": m["id"], "name": f"{m['first_name']} {m['last_name']}"} for m in g["members"]],
    })


@mcp.tool()
def delete_expense(expense_id: int) -> str:
    """Delete a Splitwise expense by ID."""
    r = httpx.delete(f"{BASE_URL}/delete_expense/{expense_id}", headers=_headers())
    r.raise_for_status()
    return json.dumps(r.json())


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        import uvicorn
        port = int(os.environ.get("PORT", "8000"))
        uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
