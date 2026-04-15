"use client";

import { ThemeToggle } from "./ThemeToggle";
import { useAuth } from "@/context/AuthContext";

export function Navbar() {
  const { user, loading, signInWithGoogle, logout } = useAuth();

  return (
    <nav className="sticky top-0 z-50 w-full bg-cur-cream/80 backdrop-blur-xl border-b border-border-primary transition-all">
      <div className="max-w-[1200px] mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-1.5">
            <div className="w-5 h-5 bg-cursor-dark rounded-[4px] flex items-center justify-center">
              <span className="text-cur-cream font-bold text-[10px]">V</span>
            </div>
            <span className="font-sans font-bold tracking-tight text-[15px] text-cursor-dark">Vaani</span>
          </div>
          
          <div className="hidden md:flex items-center gap-6 text-[13px] font-medium text-border-strong">
            <a href="#" className="hover:text-cursor-dark transition-colors">Features</a>
            <a href="#" className="hover:text-cursor-dark transition-colors">Pricing</a>
            <a href="#" className="hover:text-cursor-dark transition-colors">Docs</a>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          
          {loading ? (
            <div className="w-8 h-8 rounded-full bg-cur-surface-300 animate-pulse" />
          ) : user ? (
            <div className="flex items-center gap-3">
              {user.photoURL ? (
                <img 
                  src={user.photoURL} 
                  alt={user.displayName || "User"} 
                  className="w-8 h-8 rounded-full border border-border-primary"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-8 h-8 rounded-full bg-cur-surface-500 border border-border-primary flex items-center justify-center text-[12px] font-bold text-cursor-dark">
                  {user.displayName?.charAt(0) || user.email?.charAt(0) || "U"}
                </div>
              )}
              <button 
                onClick={logout}
                className="text-[13px] font-medium text-border-strong hover:text-cursor-dark transition-colors"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button 
              onClick={signInWithGoogle}
              className="cursor-button-primary text-[13px] py-1.5 px-3 bg-cur-surface-300 border border-border-primary hover:border-border-medium transition-all"
            >
              Sign In
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
