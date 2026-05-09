# gr-splitwise-mcp

MCP server for Splitwise. Create and manage expenses, splits, and groups directly from Claude — no manual entry.

## Tools

| Tool | What it does |
|---|---|
| `list_groups` | List all your Splitwise groups with IDs |
| `list_group_members` | List members of a group with user IDs |
| `create_group` | Create a new group and add members |
| `create_expense` | Create an expense with per-user splits, date, and notes |
| `update_expense` | Update any field on an existing expense |
| `delete_expense` | Delete an expense by ID |

## Setup

### 1. Get your Splitwise API key
Go to [https://secure.splitwise.com/apps](https://secure.splitwise.com/apps), create a new app, and copy the API key.

### 2. Add to Claude Desktop

```json
{
  "mcpServers": {
    "splitwise": {
      "command": "uvx",
      "args": ["gr-splitwise-mcp"],
      "env": {
        "SPLITWISE_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 3. Add to Claude Code

```bash
claude mcp add splitwise -e SPLITWISE_API_KEY=your-api-key-here -- uvx gr-splitwise-mcp
```

## Usage examples

**Create an expense with a custom split:**
```
Create a Splitwise expense for dinner at Zaika, $259.59, in group 97230678.
I paid. Split 75% to me (user 94211279) and 25% to Suhas (user 24465843).
Date: May 2, notes: "Niagara Falls trip dinner"
```

**Create a group:**
```
Create a Splitwise group called "Barcelona Trip 2026", type trip,
and add user 24465843 as a member.
```

**Update an expense date/notes:**
```
Update expense 4451638821 — set date to 2026-03-19 and notes to "Turo car rental booking"
```

## Notes

- Dates are automatically normalized to noon UTC to avoid timezone display issues in the Splitwise app
- All splits must sum exactly to the total cost
- Use `list_groups` and `list_group_members` to find IDs before creating expenses
