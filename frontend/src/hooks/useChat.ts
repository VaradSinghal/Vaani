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
  setDoc
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

  const createSession = async (title: string = "New Conversation") => {
    if (!user) return null;

    const sessionRef = await addDoc(collection(db, "users", user.uid, "sessions"), {
      title,
      createdAt: serverTimestamp(),
    });

    return sessionRef.id;
  };

  const addMessage = async (sessId: string, role: "User" | "Agent", text: string) => {
    if (!user || !sessId) return;

    await addDoc(collection(db, "users", user.uid, "sessions", sessId, "messages"), {
      role,
      text,
      createdAt: serverTimestamp(),
    });
  };

  return {
    sessions,
    messages,
    loading,
    createSession,
    addMessage
  };
}
