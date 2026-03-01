import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { sql } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const body = await request.json();

    const playerRows = await db.execute(
      sql`SELECT id FROM players WHERE id = ${id} AND is_npc = TRUE`
    );
    if (!(playerRows.rows[0] as any)) {
      return NextResponse.json({ error: "NPC not found" }, { status: 404 });
    }

    const gameRows = await db.execute(
      sql`SELECT id FROM game_states WHERE player_id = ${id} AND status = 'active'`
    );
    const gameRow = gameRows.rows[0] as any;
    if (!gameRow) {
      return NextResponse.json({ error: "No active game for NPC" }, { status: 404 });
    }

    if (body.firstName !== undefined) {
      await db.execute(sql`
        UPDATE players SET first_name = ${body.firstName.slice(0, 255)}, updated_at = NOW() WHERE id = ${id}
      `);
    }

    if (body.displayName !== undefined) {
      await db.execute(sql`
        UPDATE game_states SET display_name = ${body.displayName.slice(0, 40)}, updated_at = NOW() WHERE id = ${gameRow.id}
      `);
    }
    if (body.settlementName !== undefined) {
      await db.execute(sql`
        UPDATE game_states SET settlement_name = ${body.settlementName.slice(0, 100)}, updated_at = NOW() WHERE id = ${gameRow.id}
      `);
    }
    if (body.zone !== undefined) {
      await db.execute(sql`
        UPDATE game_states SET zone = ${body.zone}, updated_at = NOW() WHERE id = ${gameRow.id}
      `);
    }
    if (body.population !== undefined) {
      await db.execute(sql`
        UPDATE game_states SET population = ${body.population}, updated_at = NOW() WHERE id = ${gameRow.id}
      `);
    }
    if (body.food !== undefined) {
      await db.execute(sql`
        UPDATE game_states SET food = ${body.food}, updated_at = NOW() WHERE id = ${gameRow.id}
      `);
    }
    if (body.scrap !== undefined) {
      await db.execute(sql`
        UPDATE game_states SET scrap = ${body.scrap}, updated_at = NOW() WHERE id = ${gameRow.id}
      `);
    }
    if (body.gold !== undefined) {
      await db.execute(sql`
        UPDATE game_states SET gold = ${body.gold}, updated_at = NOW() WHERE id = ${gameRow.id}
      `);
    }

    const updated = await db.execute(sql`
      SELECT gs.*, p.first_name
      FROM game_states gs
      JOIN players p ON p.id = gs.player_id
      WHERE gs.id = ${gameRow.id}
    `);

    return NextResponse.json({ npc: updated.rows[0] });
  } catch (error) {
    console.error("Update NPC error:", error);
    return NextResponse.json(
      { error: "Failed to update NPC" },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const player = await db.execute(
      sql`SELECT id FROM players WHERE id = ${id} AND is_npc = TRUE`
    );
    if (!(player.rows[0] as any)) {
      return NextResponse.json({ error: "NPC not found" }, { status: 404 });
    }

    await db.execute(sql`DELETE FROM players WHERE id = ${id}`);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Delete NPC error:", error);
    return NextResponse.json(
      { error: "Failed to delete NPC" },
      { status: 500 }
    );
  }
}
