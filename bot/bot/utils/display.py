"""Display name resolution for shared-world features."""

from __future__ import annotations


def get_display_name(
    game_row: dict | None = None,
    player_row: dict | None = None,
) -> str:
    """Resolve the display name for a player in shared contexts.

    Priority: game_states.display_name -> players.first_name -> @players.username
    """
    if game_row and game_row.get("display_name"):
        return str(game_row["display_name"]).strip()
    if player_row and player_row.get("first_name"):
        return str(player_row["first_name"]).strip()
    if player_row and player_row.get("username"):
        return f"@{player_row['username']}"
    return "Survivor"
