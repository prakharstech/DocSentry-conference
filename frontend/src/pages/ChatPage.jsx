import React, { useState, useEffect, useRef } from 'react';
import { Send, Shield, Search, Loader2, CheckCircle2, FileText, Info, MessageSquare, Trash2, Download, Lock } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useDocSentry } from '../context/DocSentryContext';
import PrivacyLevelSelector from '../components/PrivacyLevelSelector';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ChatPage = () => {
  const {
    messages, setMessages,
    file, setFile,
    isReady, setIsReady,
    uploadStats, setUploadStats,
    currentDocText, setCurrentDocText,
    currentAnonymizedText, setCurrentAnonymizedText,
    currentDocFindings, setCurrentDocFindings,
  } = useDocSentry();

  const [isLoading, setIsLoading]   = useState(false);
  const [query, setQuery]           = useState('');
  const [privacyLevel, setPrivacyLevel] = useState('GENERALIZE');
  const messagesEndRef = useRef(null);
  const fileInputRef   = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileChange = (e) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
      setIsReady(false);
      setUploadStats(null);
    }
  };

  const handleDownload = () => {
    if (!currentAnonymizedText) return;
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([currentAnonymizedText], { type: 'text/plain' }));
    a.download = 'redacted_document.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsLoading(true);
    setMessages([...messages, { sender: 'ai', text: `🔄 **ScannerAgent** is analyzing "${file.name}" for PII...`, type: 'loading' }]);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('privacy_level', privacyLevel);

    try {
      const res  = await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();

      setUploadStats(data);
      setIsReady(true);
      setCurrentDocText(data.raw_text);
      setCurrentAnonymizedText(data.anonymized_text);
      setCurrentDocFindings(data.findings);

      const levelLabels = { SYNTHETIC: 'Synthetic Fakes', GENERALIZE: 'Category Tags', REDACT: 'Full Redaction' };
      setMessages([...messages, {
        sender: 'ai',
        text: `### ✅ Document Processed\n\n**ScannerAgent** identified **${data.pii_count}** PII entities across **${data.pii_types.length}** categories.\n\n**Privacy Mode:** ${levelLabels[data.privacy_level || privacyLevel]}\n**Detected Types:** ${data.pii_types.join(', ')}\n\nThe document has been anonymized and stored in the RAG vector store. Ask me anything about it.`,
        type: 'success'
      }]);
    } catch (err) {
      console.error(err);
      setMessages([...messages, { sender: 'ai', text: '❌ Failed to process document. Check if the backend is running.', type: 'error' }]);
    }
    setIsLoading(false);
  };

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim() || !isReady || isLoading) return;

    const userMsg = { sender: 'user', text: query };
    setMessages([...messages, userMsg]);
    setQuery('');
    setIsLoading(true);

    try {
      const res  = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg.text }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { sender: 'ai', text: data.answer, chunks: data.source_chunks }]);
    } catch {
      setMessages(prev => [...prev, { sender: 'ai', text: '❌ Error: Could not get a response from the secure RAG agent.' }]);
    }
    setIsLoading(false);
  };

  return (
    <div className="flex h-full animate-fadeIn">

      {/* ── Main Chat Area ─────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col bg-white border-r border-slate-200">
        {/* Chat header */}
        <header className="h-16 border-b border-slate-200 flex items-center justify-between px-6 bg-white/80 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-200">
              <MessageSquare className="w-4 h-4 text-white" />
            </div>
            <h2 className="font-bold text-slate-800">Secure RAG Chat</h2>
          </div>
          {isReady && (
            <div className="flex items-center gap-2 px-3 py-1 bg-green-50 rounded-full border border-green-100">
              <CheckCircle2 className="w-3 h-3 text-green-500" />
              <span className="text-[10px] font-bold text-green-600 uppercase tracking-tighter">Secure Link Active</span>
            </div>
          )}
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-md mx-auto opacity-60">
              <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center">
                <Shield className="w-8 h-8 text-slate-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-700">Ready to Secure Your Data</h3>
                <p className="text-sm text-slate-500">Upload a sensitive document to start an anonymized research session.</p>
              </div>
              {!file && (
                <button
                  onClick={() => fileInputRef.current.click()}
                  className="px-6 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all shadow-lg shadow-blue-100 flex items-center gap-2"
                >
                  <FileText className="w-4 h-4" /> Select PDF
                </button>
              )}
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-2xl p-4 shadow-sm border ${
                  msg.sender === 'user'
                    ? 'bg-blue-600 text-white border-blue-700 rounded-br-none'
                    : msg.type === 'error'
                      ? 'bg-rose-50 border-rose-100 text-rose-700 rounded-bl-none'
                      : 'bg-slate-50 border-slate-100 text-slate-800 rounded-bl-none'
                }`}>
                  <div className="prose prose-sm prose-slate max-w-none prose-headings:text-inherit prose-p:leading-relaxed">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>
                  </div>
                  {msg.chunks && (
                    <div className="mt-4 pt-4 border-t border-slate-200">
                      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2">
                        Anonymized Source Chunks ({msg.chunks.length})
                      </label>
                      <div className="space-y-2">
                        {msg.chunks.map((c, i) => (
                          <div key={i} className="text-[10px] bg-white p-2 rounded-lg border border-slate-200 text-slate-500 italic leading-normal">
                            "{c.text}"
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Query input */}
        <footer className="p-6 bg-white border-t border-slate-200">
          <form onSubmit={handleQuery} className="relative max-w-4xl mx-auto">
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              disabled={!isReady || isLoading}
              placeholder={isReady ? 'Ask a question about the document...' : 'Upload document first'}
              className="w-full pl-6 pr-14 py-4 bg-slate-100 border-none rounded-2xl focus:ring-2 focus:ring-blue-500 outline-none transition-all text-sm font-medium disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!isReady || isLoading || !query.trim()}
              className="absolute right-2 top-2 w-10 h-10 bg-blue-600 text-white rounded-xl flex items-center justify-center hover:bg-blue-700 disabled:bg-slate-300 transition-all shadow-md"
            >
              {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
          </form>
        </footer>
      </div>

      {/* ── Right Sidebar: Insights Only ───────────────────────────────── */}
      <aside className="w-80 bg-slate-50 flex flex-col overflow-y-auto border-l border-slate-100">
        <div className="px-6 py-4 border-b border-slate-200">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Document Insights</p>
        </div>

        <div className="p-6 space-y-8">

          {/* Document session card */}
          <section>
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-4">Session</label>
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center">
                  <FileText className="w-5 h-5 text-slate-500" />
                </div>
                <div className="overflow-hidden">
                  <p className="text-xs font-bold text-slate-800 truncate">{file ? file.name : 'No file'}</p>
                  <p className="text-[10px] text-slate-400 font-medium">
                    {file ? `${(file.size / 1024).toFixed(1)} KB` : 'Select a PDF to begin'}
                  </p>
                </div>
              </div>

              <input type="file" ref={fileInputRef} onChange={handleFileChange} hidden accept=".pdf" />

              {/* Privacy selector — before upload */}
              {!isReady && (
                <div>
                  <PrivacyLevelSelector selected={privacyLevel} onChange={setPrivacyLevel} disabled={isLoading} />
                </div>
              )}

              {/* Privacy mode badge — after upload */}
              {isReady && uploadStats && (
                <div className="flex items-center gap-2 px-3 py-2 bg-slate-100 rounded-xl border border-slate-200">
                  <Lock className="w-3 h-3 text-slate-500 shrink-0" />
                  <div>
                    <p className="text-[9px] font-bold text-slate-400 uppercase">Active Privacy Mode</p>
                    <p className="text-[11px] font-black text-slate-700">
                      {uploadStats.privacy_level === 'SYNTHETIC' ? '🔬 Synthetic Fakes'
                        : uploadStats.privacy_level === 'REDACT' ? '🔒 Full Redaction'
                        : '🏷️ Category Tags'}
                    </p>
                  </div>
                </div>
              )}

              {/* Action buttons */}
              {!isReady ? (
                <button
                  onClick={() => file ? handleUpload() : fileInputRef.current.click()}
                  disabled={isLoading}
                  className="w-full py-2.5 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
                >
                  {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
                  {file ? 'Analyze PDF' : 'Select PDF'}
                </button>
              ) : (
                <div className="space-y-2">
                  <button
                    onClick={handleDownload}
                    className="w-full py-2.5 bg-green-600 text-white rounded-xl text-xs font-bold hover:bg-green-700 transition-all shadow-md flex items-center justify-center gap-2"
                  >
                    <Download className="w-3 h-3" /> Download Redacted Doc
                  </button>
                  <button
                    onClick={() => { setFile(null); setIsReady(false); setMessages([]); setUploadStats(null); setPrivacyLevel('GENERALIZE'); }}
                    className="w-full py-2.5 bg-white text-slate-500 rounded-xl text-xs font-bold border border-slate-200 hover:bg-slate-50 transition-all flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-3 h-3" /> Reset Session
                  </button>
                </div>
              )}
            </div>
          </section>

          {/* Scanner insights — post-upload */}
          {uploadStats && (
            <section className="animate-fadeIn">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block mb-4">ScannerAgent Insights</label>
              <div className="space-y-3">
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
                  <span className="text-[10px] font-bold text-slate-500 flex items-center gap-2">
                    <Shield className="w-3 h-3 text-blue-500" /> PII Entities Detected
                  </span>
                  <span className="text-lg font-black text-slate-800">{uploadStats.pii_count}</span>
                </div>
                <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
                  <span className="text-[10px] font-bold text-slate-500 flex items-center gap-2 mb-3">
                    <Info className="w-3 h-3 text-amber-500" /> PII Categories
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {uploadStats.pii_types.map(t => (
                      <span key={t} className="px-2 py-1 bg-slate-100 text-[10px] font-bold text-slate-600 rounded-md border border-slate-200">{t}</span>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Link to Evaluation Dashboard */}
          {isReady && (
            <section>
              <a
                href="/evaluation"
                className="flex items-center justify-between w-full px-4 py-3 bg-blue-600 text-white rounded-2xl text-xs font-bold hover:bg-blue-700 transition-all shadow-md"
              >
                <span>Run Full Evaluation →</span>
                <span className="text-[10px] opacity-70">9 metrics</span>
              </a>
            </section>
          )}

        </div>
      </aside>
    </div>
  );
};

export default ChatPage;
