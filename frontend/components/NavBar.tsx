"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { clearToken, getToken, getUserRole } from "@/lib/auth";

export default function NavBar() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [role, setRole] = useState<string | null>(null);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    setLoggedIn(!!getToken());
    setRole(getUserRole());
  }, [pathname]);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  if (!loggedIn) return null;

  return (
    <nav className="flex items-center justify-between border-b bg-white px-8 py-4">
      <div className="flex gap-6 text-sm font-medium">
        <Link href="/po-lines">PO Lines</Link>
        <Link href="/dashboard">Dashboard</Link>
        {role === "administrator" && (
          <Link href="/admin/deletion-requests">Deletion Requests</Link>
        )}
      </div>
      <button onClick={handleLogout} className="text-sm text-zinc-600 hover:text-black">
        Log out
      </button>
    </nav>
  );
}