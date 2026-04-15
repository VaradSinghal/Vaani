"use client";

import { Sidebar } from "@/components/Sidebar";
import { ChatInterface } from "@/components/ChatInterface";
import { useAuth } from "@/context/AuthContext";
import { useRouter, useParams } from "next/navigation";
import { useEffect } from "react";

export default function SessionPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;

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
        <ChatInterface sessionId={sessionId} />
      </main>
    </div>
  );
}
