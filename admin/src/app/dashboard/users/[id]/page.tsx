import { db } from "@/lib/db";
import { sql } from "drizzle-orm";
import { notFound } from "next/navigation";
import Link from "next/link";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function UserDetailPage({ params }: PageProps) {
  const { id } = await params;

  // Fetch player
  const playerRows = await db.execute(
    sql`SELECT * FROM players WHERE id = ${id} LIMIT 1`
  );
  const player = playerRows.rows[0] as any;

  if (!player) {
    notFound();
  }

  // Fetch games and payments in parallel
  const [gamesResult, paymentsResult] = await Promise.all([
    db.execute(sql`
      SELECT
        id, status, turn_number, settlement_name,
        player_class, level, xp, zone, gold,
        skill_points, skills,
        population, food, scrap, morale, defense,
        started_at, ended_at
      FROM game_states
      WHERE player_id = ${id}
      ORDER BY started_at DESC
      LIMIT 50
    `),
    db.execute(sql`
      SELECT
        id, payment_type, status, amount, currency,
        stars_amount, premium_days, created_at, completed_at
      FROM payments
      WHERE player_id = ${id}
      ORDER BY created_at DESC
      LIMIT 50
    `),
  ]);

  const games = gamesResult.rows as any[];
  const paymentsList = paymentsResult.rows as any[];
  const commProfile =
    typeof player.comm_profile === "string"
      ? JSON.parse(player.comm_profile)
      : player.comm_profile || {};

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link
          href="/dashboard/users"
          className="text-neutral-500 hover:text-neutral-300 transition-colors"
        >
          &larr; Users
        </Link>
        <span className="text-neutral-700">/</span>
        <h1 className="text-2xl font-bold text-white">
          {player.username || player.first_name || "Anonymous"}
        </h1>
        {player.is_banned && (
          <span className="text-xs bg-red-900/40 text-red-400 px-2 py-1 rounded">
            Banned
          </span>
        )}
      </div>

      {/* Profile Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <h2 className="text-sm font-medium text-neutral-400 mb-4">
            Profile
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-neutral-500">Telegram ID</dt>
              <dd className="text-white font-mono text-sm">
                {player.telegram_id}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-neutral-500">Username</dt>
              <dd className="text-white">
                {player.username ? `@${player.username}` : "-"}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-neutral-500">First Name</dt>
              <dd className="text-white">{player.first_name || "-"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-neutral-500">Language</dt>
              <dd className="text-white uppercase">{player.language}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-neutral-500">Joined</dt>
              <dd className="text-white">
                {new Date(player.created_at).toLocaleString()}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-neutral-500">Turns Today</dt>
              <dd className="text-white">{player.turns_today}</dd>
            </div>
          </dl>
        </div>

        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <h2 className="text-sm font-medium text-neutral-400 mb-4">
            Premium & Communication
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between">
              <dt className="text-neutral-500">Premium</dt>
              <dd>
                {player.is_premium ? (
                  <span className="text-amber-400">Active</span>
                ) : (
                  <span className="text-neutral-600">No</span>
                )}
              </dd>
            </div>
            {player.premium_expires && (
              <div className="flex justify-between">
                <dt className="text-neutral-500">Expires</dt>
                <dd className="text-white">
                  {new Date(player.premium_expires).toLocaleDateString()}
                </dd>
              </div>
            )}
          </dl>

          {Object.keys(commProfile).length > 0 && (
            <div className="mt-4 pt-4 border-t border-neutral-800">
              <h3 className="text-xs font-medium text-neutral-500 mb-2 uppercase tracking-wider">
                Communication Profile
              </h3>
              <pre className="text-xs text-neutral-400 bg-neutral-800 rounded-lg p-3 overflow-auto max-h-48">
                {JSON.stringify(commProfile, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Active Game Details */}
      {games.filter((g: any) => g.status === "active").length > 0 && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5 mb-6">
          <h2 className="text-sm font-medium text-neutral-400 mb-4">
            Active Game
          </h2>
          {games
            .filter((g: any) => g.status === "active")
            .slice(0, 1)
            .map((game: any) => {
              const skills =
                typeof game.skills === "string"
                  ? JSON.parse(game.skills)
                  : game.skills || {};
              const classEmoji: Record<string, string> = {
                scavenger: "🔍",
                warden: "🛡",
                trader: "💰",
                diplomat: "🕊",
                medic: "💊",
              };
              return (
                <div key={game.id}>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
                    <div>
                      <span className="text-neutral-500 text-xs block">
                        Settlement
                      </span>
                      <span className="text-amber-400 font-medium">
                        {game.settlement_name}
                      </span>
                    </div>
                    <div>
                      <span className="text-neutral-500 text-xs block">
                        Class
                      </span>
                      <span className="text-white">
                        {classEmoji[game.player_class] || ""}{" "}
                        {game.player_class || "—"}
                      </span>
                    </div>
                    <div>
                      <span className="text-neutral-500 text-xs block">
                        Level / Zone
                      </span>
                      <span className="text-white">
                        ⭐ {game.level} / Zone {game.zone}
                      </span>
                    </div>
                    <div>
                      <span className="text-neutral-500 text-xs block">
                        Week
                      </span>
                      <span className="text-white">{game.turn_number}</span>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 mb-4">
                    <div className="bg-neutral-800 rounded-lg p-3 text-center">
                      <div className="text-xs text-neutral-500">Pop</div>
                      <div className="text-white font-bold">
                        👥 {game.population}
                      </div>
                    </div>
                    <div className="bg-neutral-800 rounded-lg p-3 text-center">
                      <div className="text-xs text-neutral-500">Food</div>
                      <div className="text-white font-bold">
                        🌾 {game.food}
                      </div>
                    </div>
                    <div className="bg-neutral-800 rounded-lg p-3 text-center">
                      <div className="text-xs text-neutral-500">Scrap</div>
                      <div className="text-white font-bold">
                        🔩 {game.scrap}
                      </div>
                    </div>
                    <div className="bg-neutral-800 rounded-lg p-3 text-center">
                      <div className="text-xs text-neutral-500">Gold</div>
                      <div className="text-amber-400 font-bold">
                        💰 {game.gold}
                      </div>
                    </div>
                    <div className="bg-neutral-800 rounded-lg p-3 text-center">
                      <div className="text-xs text-neutral-500">Morale</div>
                      <div className="text-white font-bold">
                        😊 {game.morale}
                      </div>
                    </div>
                    <div className="bg-neutral-800 rounded-lg p-3 text-center">
                      <div className="text-xs text-neutral-500">Defense</div>
                      <div className="text-white font-bold">
                        🛡 {game.defense}
                      </div>
                    </div>
                  </div>
                  {Object.keys(skills).length > 0 && (
                    <div>
                      <span className="text-neutral-500 text-xs block mb-2">
                        Skills ({game.skill_points} points available)
                      </span>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(skills).map(([skillId, rank]) => (
                          <span
                            key={skillId}
                            className="text-xs bg-indigo-900/40 text-indigo-300 px-2 py-1 rounded-full"
                          >
                            {skillId.replace(/_/g, " ")} ×{String(rank)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      )}

      {/* Game History */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden mb-6">
        <div className="px-5 py-4 border-b border-neutral-800">
          <h2 className="text-sm font-medium text-neutral-400">
            Game History ({games.length})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Settlement
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Class
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Level
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Status
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Weeks
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Resources
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Started
                </th>
              </tr>
            </thead>
            <tbody>
              {games.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-8 text-center text-neutral-600"
                  >
                    No games played
                  </td>
                </tr>
              ) : (
                games.map((game: any) => (
                  <tr
                    key={game.id}
                    className="border-b border-neutral-800/50 hover:bg-neutral-800/30"
                  >
                    <td className="px-4 py-3 text-white font-medium">
                      {game.settlement_name}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {game.player_class || "—"}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      L{game.level} Z{game.zone}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={game.status} />
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {game.turn_number}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs font-mono">
                      👥{game.population} 🌾{game.food} 🔩{game.scrap} 💰
                      {game.gold}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs">
                      {new Date(game.started_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Payment History */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-neutral-800">
          <h2 className="text-sm font-medium text-neutral-400">
            Payment History ({paymentsList.length})
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Type
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Status
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Amount
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Stars
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Premium Days
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              {paymentsList.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-neutral-600"
                  >
                    No payments
                  </td>
                </tr>
              ) : (
                paymentsList.map((payment) => (
                  <tr
                    key={payment.id}
                    className="border-b border-neutral-800/50 hover:bg-neutral-800/30"
                  >
                    <td className="px-4 py-3 text-white capitalize">
                      {payment.payment_type}
                    </td>
                    <td className="px-4 py-3">
                      <PaymentStatusBadge status={payment.status} />
                    </td>
                    <td className="px-4 py-3 text-white font-mono">
                      {payment.amount} {payment.currency}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {payment.stars_amount || "-"}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {payment.premium_days}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs">
                      {new Date(payment.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: "bg-blue-900/40 text-blue-400",
    won: "bg-green-900/40 text-green-400",
    lost: "bg-red-900/40 text-red-400",
    abandoned: "bg-neutral-800 text-neutral-500",
  };

  return (
    <span
      className={`text-xs px-2 py-0.5 rounded-full ${styles[status] || styles.abandoned}`}
    >
      {status}
    </span>
  );
}

function PaymentStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-green-900/40 text-green-400",
    pending: "bg-yellow-900/40 text-yellow-400",
    failed: "bg-red-900/40 text-red-400",
    refunded: "bg-neutral-800 text-neutral-500",
  };

  return (
    <span
      className={`text-xs px-2 py-0.5 rounded-full ${styles[status] || styles.pending}`}
    >
      {status}
    </span>
  );
}
