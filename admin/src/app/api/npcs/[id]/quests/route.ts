import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { sql } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: npcPlayerId } = await params;
  try {
    const rows = await db.execute(sql`
      SELECT id, quest_key, name, description, requirements, rewards, is_active
      FROM npc_quests
      WHERE npc_player_id = ${npcPlayerId}
      ORDER BY quest_key
    `);
    return NextResponse.json({ quests: rows.rows });
  } catch (error) {
    console.error("List quests error:", error);
    return NextResponse.json(
      { error: "Failed to list quests" },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id: npcPlayerId } = await params;
  try {
    const body = await request.json();
    const { questKey, name, description, requirements = {}, rewards = {} } = body;

    if (!questKey || !name || !description) {
      return NextResponse.json(
        { error: "questKey, name, description required" },
        { status: 400 }
      );
    }

    const result = await db.execute(sql`
      INSERT INTO npc_quests (npc_player_id, quest_key, name, description, requirements, rewards)
      VALUES (
        ${npcPlayerId},
        ${questKey.slice(0, 80)},
        ${name.slice(0, 100)},
        ${description},
        ${JSON.stringify(requirements)}::jsonb,
        ${JSON.stringify(rewards)}::jsonb
      )
      RETURNING *
    `);
    const quest = result.rows[0];
    return NextResponse.json({ quest });
  } catch (error) {
    console.error("Create quest error:", error);
    return NextResponse.json(
      { error: "Failed to create quest" },
      { status: 500 }
    );
  }
}
