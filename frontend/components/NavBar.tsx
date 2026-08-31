"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth";
import { useAuth } from "@/lib/useAuth";

const LINKS = [
  { href: "/po-lines", label: "PO Lines", adminOnly: false },
  { href: "/dashboard", label: "Dashboard", adminOnly: false },
  { href: "/admin/deletion-requests", label: "Deletion Requests", adminOnly: true },
  { href: "/admin/thresholds", label: "Alert Thresholds", adminOnly: true },
  { href: "/admin/users", label: "Users", adminOnly: true },
];

export default function NavBar() {
  const { loggedIn, isAdmin } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  if (!loggedIn) return null;

  return (
    <nav className="flex items-center justify-between border-b bg-white px-8 py-4">
      <div className="flex gap-6 text-sm font-medium">
        {LINKS.filter((l) => !l.adminOnly || isAdmin).map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className={pathname === l.href ? "text-black" : "text-zinc-500 hover:text-black"}
          >
            {l.label}
          </Link>
        ))}
      </div>
      <button onClick={handleLogout} className="text-sm text-zinc-600 hover:text-black">
        Log out
      </button>
    </nav>
  );
}
