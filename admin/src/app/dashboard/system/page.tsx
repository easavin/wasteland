import { db } from "@/lib/db";
import { sql } from "drizzle-orm";

export const dynamic = "force-dynamic";

async function getDbHealth() {
  try {
    const start = Date.now();
    await db.execute(sql`SELECT 1`);
    const latency = Date.now() - start;
    return { connected: true, latencyMs: latency };
  } catch (error) {
    return { connected: false, latencyMs: 0, error: String(error) };
  }
}

async function getTableCounts() {
  const result = await db.execute(sql`
    SELECT
      (SELECT COUNT(*) FROM players) as players,
      (SELECT COUNT(*) FROM game_states) as games,
      (SELECT COUNT(*) FROM turn_history) as turns,
      (SELECT COUNT(*) FROM payments) as payments,
      (SELECT COUNT(*) FROM analytics_events) as events,
      (SELECT COUNT(*) FROM admin_users) as admins
  `);
  return result.rows[0] as any;
}

async function getRecentErrors() {
  const result = await db.execute(sql`
    SELECT
      id,
      event_type,
      event_data,
      player_id,
      created_at
    FROM analytics_events
    WHERE event_type ILIKE '%error%'
       OR event_type ILIKE '%fail%'
    ORDER BY created_at DESC
    LIMIT 20
  `);
  return result.rows as any[];
}

async function getDbSize() {
  try {
    const result = await db.execute(sql`
      SELECT pg_size_pretty(pg_database_size(current_database())) as size
    `);
    return result.rows[0]?.size as string || "Unknown";
  } catch {
    return "Unavailable";
  }
}

export default async function SystemPage() {
  const [health, counts, recentErrors, dbSize] = await Promise.all([
    getDbHealth(),
    getTableCounts(),
    getRecentErrors(),
    getDbSize(),
  ]);

  const tables = [
    { name: "players", count: counts.players },
    { name: "game_states", count: counts.games },
    { name: "turn_history", count: counts.turns },
    { name: "payments", count: counts.payments },
    { name: "analytics_events", count: counts.events },
    { name: "admin_users", count: counts.admins },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">System</h1>

      {/* Health Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <div className="text-neutral-500 text-sm mb-2">
            Database Connection
          </div>
          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${health.connected ? "bg-green-500" : "bg-red-500"}`}
            />
            <span
              className={`text-lg font-bold ${health.connected ? "text-green-400" : "text-red-400"}`}
            >
              {health.connected ? "Connected" : "Disconnected"}
            </span>
          </div>
          {health.connected && (
            <div className="text-neutral-600 text-xs mt-1">
              Latency: {health.latencyMs}ms
            </div>
          )}
        </div>

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <div className="text-neutral-500 text-sm mb-2">Database Size</div>
          <div className="text-lg font-bold text-white">{dbSize}</div>
        </div>

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <div className="text-neutral-500 text-sm mb-2">Total Events</div>
          <div className="text-lg font-bold text-white">
            {Number(counts.events).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Table Row Counts */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 mb-6">
        <h2 className="text-sm font-medium text-neutral-400 mb-4">
          Table Row Counts
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {tables.map((t) => (
            <div key={t.name} className="text-center">
              <div className="text-xs text-neutral-500 mb-1 font-mono">
                {t.name}
              </div>
              <div className="text-lg font-bold text-white">
                {Number(t.count).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Errors */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-neutral-800">
          <h2 className="text-sm font-medium text-neutral-400">
            Recent Error Events
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Event Type
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Player ID
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Data
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Time
                </th>
              </tr>
            </thead>
            <tbody>
              {recentErrors.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="px-4 py-8 text-center text-neutral-600"
                  >
                    No error events found
                  </td>
                </tr>
              ) : (
                recentErrors.map((err: any) => {
                  const data =
                    typeof err.event_data === "string"
                      ? JSON.parse(err.event_data)
                      : err.event_data;

                  return (
                    <tr
                      key={err.id}
                      className="border-b border-neutral-800/50 hover:bg-neutral-800/30"
                    >
                      <td className="px-4 py-3 text-red-400 font-mono text-xs">
                        {err.event_type}
                      </td>
                      <td className="px-4 py-3 text-neutral-500 font-mono text-xs">
                        {err.player_id
                          ? err.player_id.substring(0, 8) + "..."
                          : "-"}
                      </td>
                      <td className="px-4 py-3 text-neutral-400 text-xs max-w-md truncate">
                        {JSON.stringify(data)}
                      </td>
                      <td className="px-4 py-3 text-neutral-500 text-xs whitespace-nowrap">
                        {new Date(err.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
