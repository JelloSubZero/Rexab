"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { clsx } from "@/lib/clsx";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "🏠" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { user, isLoading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <span
          className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent"
          aria-hidden="true"
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg">
      <div className="flex min-h-screen">
        <aside className="hidden w-56 shrink-0 border-r border-border bg-card md:flex md:flex-col">
          <div className="px-6 py-5 text-lg font-semibold tracking-tight text-primary">
            Rexab
          </div>
          <nav className="flex flex-1 flex-col gap-1 px-3">
            {NAV_ITEMS.map((item) => {
              const isActive = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-accent/10 text-accent"
                      : "text-secondary hover:bg-bg hover:text-primary",
                  )}
                >
                  <span aria-hidden="true">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>

        <div className="flex flex-1 flex-col">
          <header className="flex items-center justify-between border-b border-border bg-card px-4 py-3 md:px-8">
            <span className="text-base font-semibold text-primary md:hidden">
              Rexab
            </span>
            <span className="hidden md:block" />
            <div className="relative">
              <button
                onClick={() => setMenuOpen((open) => !open)}
                className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm font-medium text-primary hover:bg-bg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/10 text-accent">
                  {user.first_name.charAt(0).toUpperCase()}
                </span>
                {user.first_name}
                <span aria-hidden="true">▾</span>
              </button>
              {menuOpen && (
                <div
                  role="menu"
                  className="absolute right-0 z-10 mt-2 w-44 overflow-hidden rounded-lg border border-border bg-card shadow-md"
                >
                  <Link
                    href="/settings"
                    role="menuitem"
                    className="block px-4 py-2.5 text-sm text-primary hover:bg-bg"
                    onClick={() => setMenuOpen(false)}
                  >
                    Settings
                  </Link>
                  <button
                    role="menuitem"
                    onClick={() => {
                      setMenuOpen(false);
                      logout();
                      router.replace("/login");
                    }}
                    className="block w-full px-4 py-2.5 text-left text-sm text-negative hover:bg-negative-bg"
                  >
                    Log out
                  </button>
                </div>
              )}
            </div>
          </header>

          <main className="flex-1 px-4 py-6 pb-20 md:px-8 md:pb-6">
            {children}
          </main>
        </div>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-20 flex border-t border-border bg-card md:hidden">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex flex-1 flex-col items-center gap-0.5 py-2.5 text-xs font-medium",
                isActive ? "text-accent" : "text-secondary",
              )}
            >
              <span className="text-lg" aria-hidden="true">
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
