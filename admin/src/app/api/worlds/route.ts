import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { sql } from "drizzle-orm";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const rows = await db.execute(sql`SELECT id, name FROM worlds ORDER BY name`);
    return NextResponse.json({ worlds: rows.rows });
  } catch (error) {
    console.error("List worlds error:", error);
    return NextResponse.json(
      { error: "Failed to list worlds" },
      { status: 500 }
    );
  }
}
