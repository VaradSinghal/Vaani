"use client";

import { Sidebar } from "@/components/Sidebar";
import { ChatInterface } from "@/components/ChatInterface";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function HomeRoot() {
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
        {/* Empty state or redirect to new session if needed */}
        <div className="h-full flex items-center justify-center">
          <div className="text-center space-y-6 opacity-30 select-none">
             <div className="w-20 h-20 bg-cur-surface-300 rounded-3xl mx-auto flex items-center justify-center">
                <span className="font-bold text-4xl">V</span>
             </div>
             <h2 className="section-heading !text-3xl">Vaani Home</h2>
             <p className="body-standard">Select a conversation from the sidebar or start a new one.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
