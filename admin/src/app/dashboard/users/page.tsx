import { db } from "@/lib/db";
import { players, gameStates } from "@/lib/schema";
import { sql, ilike, count, eq } from "drizzle-orm";
import Link from "next/link";

export const dynamic = "force-dynamic";

interface PageProps {
  searchParams: Promise<{ page?: string; search?: string }>;
}

const PAGE_SIZE = 25;

export default async function UsersPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const page = Math.max(1, parseInt(params.page || "1"));
  const search = params.search || "";
  const offset = (page - 1) * PAGE_SIZE;

  const searchCondition = search
    ? sql`(${players.username} ILIKE ${"%" + search + "%"} OR ${players.firstName} ILIKE ${"%" + search + "%"})`
    : sql`TRUE`;

  const [rows, [{ total }]] = await Promise.all([
    db.execute(sql`
      SELECT
        p.id,
        p.telegram_id,
        p.username,
        p.first_name,
        p.language,
        p.is_premium,
        p.is_banned,
        p.created_at,
        (SELECT COUNT(*) FROM game_states g WHERE g.player_id = p.id) as games_count
      FROM players p
      WHERE ${searchCondition}
      ORDER BY p.created_at DESC
      LIMIT ${PAGE_SIZE} OFFSET ${offset}
    `),
    db.execute(sql`
      SELECT COUNT(*) as total
      FROM players p
      WHERE ${searchCondition}
    `).then((r) => r.rows as any[]),
  ]);

  const totalPages = Math.ceil(Number(total) / PAGE_SIZE);

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Users</h1>

      {/* Search */}
      <form className="mb-6">
        <div className="flex gap-3">
          <input
            name="search"
            type="text"
            defaultValue={search}
            placeholder="Search by username or name..."
            className="flex-1 max-w-sm px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
          >
            Search
          </button>
          {search && (
            <Link
              href="/dashboard/users"
              className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm font-medium transition-colors"
            >
              Clear
            </Link>
          )}
        </div>
      </form>

      {/* Table */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Username
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Telegram ID
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Language
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Premium
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Games
                </th>
                <th className="text-left px-4 py-3 text-neutral-500 font-medium">
                  Joined
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-8 text-center text-neutral-600"
                  >
                    No users found
                  </td>
                </tr>
              ) : (
                rows.rows.map((user: any) => (
                  <tr
                    key={user.id}
                    className="border-b border-neutral-800/50 hover:bg-neutral-800/30 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        href={`/dashboard/users/${user.id}`}
                        className="text-amber-400 hover:text-amber-300 font-medium"
                      >
                        {user.username || user.first_name || "Anonymous"}
                      </Link>
                      {user.is_banned && (
                        <span className="ml-2 text-xs bg-red-900/40 text-red-400 px-1.5 py-0.5 rounded">
                          banned
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-neutral-400 font-mono text-xs">
                      {user.telegram_id}
                    </td>
                    <td className="px-4 py-3 text-neutral-400 uppercase">
                      {user.language}
                    </td>
                    <td className="px-4 py-3">
                      {user.is_premium ? (
                        <span className="text-xs bg-amber-900/40 text-amber-400 px-2 py-0.5 rounded-full">
                          Premium
                        </span>
                      ) : (
                        <span className="text-neutral-600">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-neutral-400">
                      {user.games_count}
                    </td>
                    <td className="px-4 py-3 text-neutral-500 text-xs">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-neutral-500">
            Page {page} of {totalPages} ({total} users)
          </span>
          <div className="flex gap-2">
            {page > 1 && (
              <Link
                href={`/dashboard/users?page=${page - 1}${search ? `&search=${encodeURIComponent(search)}` : ""}`}
                className="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm transition-colors"
              >
                Previous
              </Link>
            )}
            {page < totalPages && (
              <Link
                href={`/dashboard/users?page=${page + 1}${search ? `&search=${encodeURIComponent(search)}` : ""}`}
                className="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm transition-colors"
              >
                Next
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
