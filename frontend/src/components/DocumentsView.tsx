"use client";

import { useDocuments } from "../hooks/useDocuments";
import { useAuth } from "../context/AuthContext";
import { useRef, useState } from "react";

export function DocumentsView() {
  const { user } = useAuth();
  const { documents, uploading, uploadProgress, uploadDocument, deleteDocument } = useDocuments();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadDocument(file, "en-IN", user?.uid || "anonymous");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      await uploadDocument(file, "en-IN", user?.uid || "anonymous");
    }
  };

  return (
    <div className="flex flex-col h-full bg-cur-cream overflow-y-auto">
      {/* Header */}
      <header className="flex-none px-8 h-20 border-b border-border-primary flex items-center justify-between sticky top-0 bg-cur-cream/80 backdrop-blur-md z-10">
        <div>
          <h1 className="section-heading !text-3xl">Knowledge Library</h1>
          <p className="body-standard text-[13px] opacity-60">
            Manage documents that Vaani uses for reasoning.
          </p>
        </div>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="px-6 py-2.5 bg-cursor-dark text-cur-cream rounded-full text-sm font-medium hover:bg-black transition-all shadow-lg active:scale-95 disabled:opacity-50"
        >
          {uploading ? "Uploading..." : "Add Document"}
        </button>
      </header>

      <div className="flex-1 max-w-5xl mx-auto w-full p-8 space-y-12">
        {/* Upload Dropzone */}
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-[32px] p-12 transition-all cursor-pointer group flex flex-col items-center justify-center text-center space-y-4 ${
            isDragging 
            ? "border-cur-orange bg-cur-orange/5 scale-[1.01]" 
            : "border-border-primary bg-cur-surface-300 hover:border-cur-orange/40 hover:bg-cur-orange/[0.02]"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            className="hidden"
          />
          <div className="w-16 h-16 bg-white rounded-2xl shadow-sm flex items-center justify-center transition-transform group-hover:scale-110">
             <svg className="w-8 h-8 text-cur-orange" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
             </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-cursor-dark">
              {uploading ? "Processing knowledge..." : "Drop files here or click to upload"}
            </h3>
            <p className="body-standard text-sm opacity-50 mt-1">
              Supports PDF, PNG, JPG, TXT, and Markdown
            </p>
          </div>
          
          {uploadProgress && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-cur-cream/60 backdrop-blur-[2px] rounded-[32px] animate-cursor">
               <div className="w-48 h-1.5 bg-border-primary rounded-full overflow-hidden">
                  <div className="h-full bg-cur-orange animate-progress-indefinite" />
               </div>
               <span className="font-mono text-xs mt-4 uppercase tracking-widest text-border-strong">{uploadProgress}</span>
            </div>
          )}
        </div>

        {/* Documents Grid */}
        <section>
          <div className="flex items-center justify-between mb-8">
            <h2 className="font-mono text-[11px] uppercase tracking-[0.2em] text-border-strong opacity-40">
              Active Documents ({documents.length})
            </h2>
          </div>

          {documents.length === 0 ? (
            <div className="py-20 text-center border border-border-primary rounded-[24px] bg-cur-surface-100/30">
               <p className="body-serif italic text-lg opacity-40">Your library is empty. Upload a file to begin.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {documents.map((doc) => (
                <div
                  key={doc.doc_id}
                  className="group relative bg-white border border-border-primary rounded-[24px] p-6 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="w-12 h-12 rounded-xl bg-cur-surface-300 flex items-center justify-center text-2xl">
                      {doc.doc_type === "invoice" ? "🧾" :
                       doc.doc_type === "receipt" ? "🧾" :
                       doc.doc_type === "report" ? "📊" :
                       doc.doc_type === "letter" ? "✉️" :
                       doc.doc_type === "resume" ? "📄" :
                       doc.doc_type === "contract" ? "📜" : "📄"}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteDocument(doc.doc_id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-2 text-red-300 hover:text-red-500 transition-all active:scale-90"
                    >
                       <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                       </svg>
                    </button>
                  </div>
                  
                  <h4 className="text-[17px] font-semibold text-cursor-dark line-clamp-1">
                    {doc.title}
                  </h4>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-2 py-0.5 rounded bg-cur-cream text-[10px] uppercase font-mono tracking-wider font-bold text-border-strong border border-border-primary">
                      {doc.doc_type}
                    </span>
                    <span className="text-[11px] text-border-strong opacity-40 font-mono">
                      {doc.fact_count} atomic facts
                    </span>
                  </div>
                  
                  <div className="mt-4 pt-4 border-t border-border-primary/50 flex items-center justify-between">
                     <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full bg-cur-success" />
                        <span className="text-[11px] font-medium opacity-60">Verified Factified</span>
                     </div>
                     <span className="text-[10px] font-mono opacity-30">ID: {doc.doc_id.slice(0, 8)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
