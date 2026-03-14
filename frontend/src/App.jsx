import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatPage from './pages/ChatPage';
import EvaluationPage from './pages/EvaluationPage';
import ExperimentPage from './pages/ExperimentPage';
import { DocSentryProvider } from './context/DocSentryContext';

function App() {
  return (
    <DocSentryProvider>
      <Router>
        <div className="fixed inset-0 bg-slate-50 flex overflow-hidden">
          {/* Sidebar Navigation */}
          <Sidebar />

          {/* Main Content Area */}
          <main className="flex-1 relative overflow-hidden flex flex-col">
            <Routes>
              <Route path="/" element={<ChatPage />} />
              <Route path="/evaluation" element={<EvaluationPage />} />
              <Route path="/experiment" element={<ExperimentPage />} />
            </Routes>
          </main>
        </div>

        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }
          .animate-fadeIn {
            animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
          }
          ::-webkit-scrollbar {
            width: 5px;
            height: 5px;
          }
          ::-webkit-scrollbar-track {
            background: transparent;
          }
          ::-webkit-scrollbar-thumb {
            background: #e2e8f0;
            border-radius: 10px;
          }
          ::-webkit-scrollbar-thumb:hover {
            background: #cbd5e1;
          }
          .prose strong { color: inherit; font-weight: 800; }
          .prose pre { background: #0f172a !important; color: #94a3b8 !important; }
        `}</style>
      </Router>
    </DocSentryProvider>
  );
}

export default App;