"use client";

import { usePathname } from "next/navigation";
import Sidebar from "./sidebar";
import Header from "./header";
import { useAuth } from "@/lib/auth";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { loading } = useAuth();
  const isLoginPage = pathname === "/login";

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-950">
        <div className="h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (isLoginPage) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
