"use client";

import { useState, useEffect, useCallback } from "react";
import { 
  collection, 
  query, 
  onSnapshot, 
  orderBy, 
  addDoc, 
  serverTimestamp, 
  where,
  Timestamp,
  doc,
  getDoc,
  setDoc,
  updateDoc
} from "firebase/firestore";
import { db } from "@/utils/firebase";
import { useAuth } from "@/context/AuthContext";

export interface ChatSession {
  id: string;
  title: string;
  createdAt: Timestamp;
}

export interface ChatMessage {
  id: string;
  role: "User" | "Agent";
  text: string;
  sources?: string[];
  createdAt: Timestamp;
}

export function useChat(sessionId?: string) {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch all sessions
  useEffect(() => {
    if (!user) return;

    const q = query(
      collection(db, "users", user.uid, "sessions"),
      orderBy("createdAt", "desc")
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const sessionList = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      })) as ChatSession[];
      setSessions(sessionList);
      setLoading(false);
    });

    return () => unsubscribe();
  }, [user]);

  // Fetch messages for active session
  useEffect(() => {
    if (!user || !sessionId) {
      setMessages([]);
      return;
    }

    const q = query(
      collection(db, "users", user.uid, "sessions", sessionId, "messages"),
      orderBy("createdAt", "asc")
    );

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const messageList = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      })) as ChatMessage[];
      setMessages(messageList);
    });

    return () => unsubscribe();
  }, [user, sessionId]);

  const createSession = async (title?: string) => {
    if (!user) return null;

    const sessionTitle = title && title !== "New Conversation" 
      ? title 
      : `Chat on ${new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}`;

    const sessionRef = await addDoc(collection(db, "users", user.uid, "sessions"), {
      title: sessionTitle,
      createdAt: serverTimestamp(),
    });

    return sessionRef.id;
  };

  const addMessage = async (sessId: string, role: "User" | "Agent", text: string, sources?: string[]) => {
    if (!user || !sessId) return;

    await addDoc(collection(db, "users", user.uid, "sessions", sessId, "messages"), {
      role,
      text,
      sources: sources || null,
      createdAt: serverTimestamp(),
    });

    if (role === "User") {
      setSessions(prev => {
        const session = prev.find(s => s.id === sessId);
        if (session && session.title.startsWith("Chat on ")) {
          // Fire and forget title update
          fetch("http://localhost:8000/api/generate-title", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
          })
          .then(res => res.json())
          .then(data => {
            if (data.title) {
              updateDoc(doc(db, "users", user.uid, "sessions", sessId), {
                title: data.title
              }).catch(console.error);
            }
          })
          .catch(console.error);
        }
        return prev;
      });
    }
  };

  return {
    sessions,
    messages,
    loading,
    createSession,
    addMessage
  };
}
