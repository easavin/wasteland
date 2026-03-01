"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clsx } from "clsx";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: "\u{1F4CA}" },
  { href: "/dashboard/users", label: "Users", icon: "\u{1F465}" },
  { href: "/dashboard/analytics", label: "Analytics", icon: "\u{1F4C8}" },
  { href: "/dashboard/revenue", label: "Revenue", icon: "\u{1F4B0}" },
  { href: "/dashboard/games", label: "Games", icon: "\u{1F3AE}" },
  { href: "/dashboard/system", label: "System", icon: "\u{2699}\u{FE0F}" },
  { href: "/dashboard/npcs", label: "NPCs", icon: "\u{1F464}" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    document.cookie = "admin_token=; path=/; max-age=0";
    router.push("/login");
  }

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-56 bg-neutral-900 border-r border-neutral-800 flex flex-col shrink-0">
        <div className="p-5 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <span className="text-xl">&#9762;</span>
            <div>
              <div className="font-bold text-white text-sm">Wasteland</div>
              <div className="text-neutral-500 text-xs">Admin Panel</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-0.5">
          {navItems.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                  isActive
                    ? "bg-amber-600/15 text-amber-400"
                    : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
                )}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-3 border-t border-neutral-800">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-neutral-400 hover:text-red-400 hover:bg-neutral-800 transition-colors w-full cursor-pointer"
          >
            <span className="text-base">&#x1F6AA;</span>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
