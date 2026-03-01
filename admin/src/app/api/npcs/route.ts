import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { sql } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const rows = await db.execute(sql`
      SELECT
        p.id AS player_id,
        p.telegram_id,
        p.first_name,
        p.username,
        gs.id AS game_id,
        gs.settlement_name,
        gs.display_name,
        gs.world_id,
        gs.zone,
        gs.population,
        gs.food,
        gs.scrap,
        gs.gold,
        gs.status
      FROM players p
      JOIN game_states gs ON gs.player_id = p.id
      WHERE p.is_npc = TRUE AND gs.status = 'active'
      ORDER BY gs.display_name
    `);
    return NextResponse.json({ npcs: rows.rows });
  } catch (error) {
    console.error("List NPCs error:", error);
    return NextResponse.json(
      { error: "Failed to list NPCs" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      displayName,
      settlementName,
      worldId,
      zone = 1,
      population = 50,
      food = 100,
      scrap = 80,
      gold = 50,
    } = body;

    if (!displayName || !settlementName || !worldId) {
      return NextResponse.json(
        { error: "displayName, settlementName, worldId required" },
        { status: 400 }
      );
    }

    const username = `npc_${displayName.toLowerCase().replace(/\s/g, "_").slice(0, 200)}`;

    const playerResult = await db.execute(sql`
      INSERT INTO players (telegram_id, username, first_name, is_npc)
      SELECT
        COALESCE((SELECT MIN(telegram_id) - 1 FROM players WHERE telegram_id < 0), -1),
        ${username},
        ${displayName.slice(0, 255)},
        TRUE
      RETURNING id, telegram_id, first_name
    `);
    const player = (playerResult.rows[0] as any);
    if (!player) {
      return NextResponse.json({ error: "Failed to create player" }, { status: 500 });
    }

    const gameResult = await db.execute(sql`
      INSERT INTO game_states (
        player_id, settlement_name, display_name, world_id, zone,
        population, food, scrap, gold
      )
      VALUES (
        ${player.id},
        ${settlementName.slice(0, 100)},
        ${displayName.slice(0, 40)},
        ${worldId},
        ${zone},
        ${population},
        ${food},
        ${scrap},
        ${gold}
      )
      RETURNING *
    `);
    const game = gameResult.rows[0] as any;

    return NextResponse.json({ npc: { ...player, game } });
  } catch (error) {
    console.error("Create NPC error:", error);
    return NextResponse.json(
      { error: "Failed to create NPC" },
      { status: 500 }
    );
  }
}
