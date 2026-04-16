"use client";

import { useAuth } from "@/context/AuthContext";
import { useChat, ChatSession } from "@/hooks/useChat";
import { useRouter, useParams, usePathname } from "next/navigation";

export function Sidebar() {
  const { user, logout } = useAuth();
  const { sessions, createSession } = useChat();
  const router = useRouter();
  const params = useParams();
  const pathname = usePathname();
  const activeSessionId = params.sessionId as string;

  const handleNewChat = async () => {
    const id = await createSession();
    if (id) {
      router.push(`/home/${id}`);
    }
  };

  return (
    <div className="w-[260px] h-screen bg-[#26251e] flex flex-col border-r border-white/5 transition-all">
      {/* Workspace Navigation */}
      <div className="px-3 py-2 space-y-1">
        <button 
          onClick={() => router.push("/home/documents")}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
            pathname === "/home/documents" 
            ? "bg-white/10 text-white" 
            : "text-white/60 hover:bg-white/5 hover:text-white/90"
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <span className="font-medium">Knowledge Library</span>
        </button>

        <button 
          onClick={() => router.push("/home/agents")}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all ${
            pathname === "/home/agents" 
            ? "bg-white/10 text-white" 
            : "text-white/60 hover:bg-white/5 hover:text-white/90"
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <span className="font-medium">Agent Studio</span>
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button 
          onClick={handleNewChat}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg border border-white/10 text-white/90 text-sm hover:bg-white/5 transition-colors group"
        >
          <svg className="w-4 h-4 text-white/60 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span className="font-medium">New Chat</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-1 scrollbar-hide">
        <h4 className="px-3 mb-4 font-mono text-[10px] uppercase tracking-widest text-white/30">Recent History</h4>
        {sessions.map((session) => (
          <button
            key={session.id}
            onClick={() => router.push(`/home/${session.id}`)}
            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all truncate ${
              activeSessionId === session.id 
              ? "bg-white/10 text-white" 
              : "text-white/60 hover:bg-white/5 hover:text-white/90"
            }`}
          >
            <div className="flex items-center gap-3">
              <svg className="w-4 h-4 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              {session.title}
            </div>
          </button>
        ))}
      </div>

      {/* User Area */}
      <div className="p-3 border-t border-white/5 bg-white/[0.02]">
        <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/80 group">
          <img 
            src={user?.photoURL || ""} 
            alt={user?.displayName || "U"} 
            className="w-8 h-8 rounded-full border border-white/10"
          />
          <div className="flex-1 truncate">
            <div className="text-xs font-medium truncate">{user?.displayName}</div>
            <button 
              onClick={() => logout()}
              className="text-[10px] text-white/40 hover:text-cur-orange transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
