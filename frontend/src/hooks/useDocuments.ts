"use client";

import { useState, useEffect, useCallback } from "react";

export interface Document {
  doc_id: string;
  filename: string;
  doc_type: string;
  title: string;
  fact_count: number;
  facts: string[];
  processed_at: string;
  error?: string;
}

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState("");

  // Fetch documents on mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:8000/api/documents");
      const data = await res.json();
      // Map vector store docs to our Document interface
      if (data.documents) {
        setDocuments(
          data.documents.map((d: any) => ({
            doc_id: d.doc_id,
            filename: "",
            doc_type: d.type,
            title: d.title,
            fact_count: d.fact_count,
            facts: [],
            processed_at: "",
          }))
        );
      }
    } catch (e) {
      console.error("Failed to fetch documents:", e);
    }
  }, []);

  const uploadDocument = useCallback(
    async (file: File, language: string = "en-IN", userId: string = "anonymous") => {
      setUploading(true);
      setUploadProgress("Uploading...");

      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("language", language);
        formData.append("user_id", userId);

        setUploadProgress("Processing document...");

        const res = await fetch("http://localhost:8000/api/upload-document", {
          method: "POST",
          body: formData,
        });

        const result: Document = await res.json();

        if (result.error) {
          setUploadProgress(`Error: ${result.error}`);
          setTimeout(() => setUploadProgress(""), 3000);
        } else {
          setUploadProgress(`✓ ${result.fact_count} facts extracted`);
          setDocuments((prev) => [result, ...prev]);
          setTimeout(() => setUploadProgress(""), 3000);
        }

        return result;
      } catch (e) {
        console.error("Upload failed:", e);
        setUploadProgress("Upload failed");
        setTimeout(() => setUploadProgress(""), 3000);
        return null;
      } finally {
        setUploading(false);
      }
    },
    []
  );

  const deleteDocument = useCallback(async (docId: string) => {
    try {
      await fetch(`http://localhost:8000/api/documents/${docId}`, {
        method: "DELETE",
      });
      setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
    } catch (e) {
      console.error("Delete failed:", e);
    }
  }, []);

  return {
    documents,
    uploading,
    uploadProgress,
    uploadDocument,
    deleteDocument,
    refreshDocuments: fetchDocuments,
  };
}
