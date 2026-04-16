"use client";

import { Sidebar } from "@/components/Sidebar";
import { DocumentsView } from "@/components/DocumentsView";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function DocumentsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/");
    }
  }, [user, loading, router]);

  if (loading || !user) return null;

  return (
    <div className="flex h-screen bg-cur-cream">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
        <DocumentsView />
      </main>
    </div>
  );
}
