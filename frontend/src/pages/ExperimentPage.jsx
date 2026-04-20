import React, { useState } from 'react';
import { FlaskConical, Play, Loader2, CheckCircle2, ChevronRight, FileText, Shield, AlertCircle, Copy, Download } from 'lucide-react';
import { useDocSentry } from '../context/DocSentryContext';
import PrivacyLevelSelector from '../components/PrivacyLevelSelector';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ExperimentPage = () => {
  const { currentDocText } = useDocSentry();
  const [numSamples, setNumSamples] = useState(5);
  const [privacyLevel, setPrivacyLevel] = useState('GENERALIZE');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(0);

  const runExperiment = async () => {
    setIsLoading(true);
    setResults(null);
    try {
      const response = await fetch(`${API_URL}/experiment/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          num_samples: numSamples,
          document_text: currentDocText || null,
          privacy_level: privacyLevel
        })
      });
      const data = await response.json();
      setResults(data);
    } catch (e) {
      console.error(e);
      alert('Experiment failed.');
    }
    setIsLoading(false);
  };

  return (
    <div className="flex flex-col h-full bg-slate-50 p-8 overflow-y-auto">
      <div className="max-w-6xl mx-auto w-full">
        <header className="mb-8 flex justify-between items-end">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Research Lab</h1>
                <p className="text-slate-500 mt-2">
                  {currentDocText ? "End-to-end multi-agent pipeline testing on uploaded document." : "End-to-end multi-agent pipeline testing on synthetic medical data."}
                </p>
            </div>
            <div className="flex items-center gap-4 bg-white p-2 rounded-2xl border shadow-sm">
                <div className="px-4">
                    <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest">Sample Size</label>
                    <input 
                        type="number" 
                        value={numSamples} 
                        onChange={(e) => setNumSamples(parseInt(e.target.value))}
                        className="w-16 font-bold text-slate-700 outline-none"
                    />
                </div>
                <button 
                    onClick={runExperiment}
                    disabled={isLoading}
                    className="bg-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-700 disabled:bg-slate-300 transition-all flex items-center gap-2 shadow-lg shadow-blue-100"
                >
                    {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                    Run Experiment
                </button>
            </div>
        </header>

        {/* Privacy Level Controls */}
        <div className="mb-6 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
          <PrivacyLevelSelector
            selected={privacyLevel}
            onChange={setPrivacyLevel}
            disabled={isLoading}
          />
        </div>

        {results ? (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Aggregate Summary */}
                <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                    {[
                        { label: 'Avg Precision', value: (results.aggregate_metrics.avg_precision * 100).toFixed(1) + '%' },
                        { label: 'Avg Recall', value: (results.aggregate_metrics.avg_recall * 100).toFixed(1) + '%' },
                        { label: 'Data Utility', value: results.aggregate_metrics.avg_utility + '/100' },
                        { label: 'Adv. Success (ASR)', value: (results.aggregate_metrics.adversarial_success_rate * 100).toFixed(1) + '%' },
                    ].map((stat, i) => (
                        <div key={i} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{stat.label}</p>
                            <p className="text-2xl font-black text-slate-900 mt-1">{stat.value}</p>
                        </div>
                    ))}
                </div>

                {/* Main Results Table */}
                <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                    <div className="p-4 bg-slate-50 border-b">
                        <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Generated Samples</h2>
                    </div>
                    <div className="flex-1 overflow-y-auto max-h-[600px]">
                        {results.results.map((r, i) => (
                            <button 
                                key={i}
                                onClick={() => setExpandedIndex(i)}
                                className={`w-full text-left p-4 border-b hover:bg-slate-50 transition-all flex items-center justify-between ${expandedIndex === i ? 'bg-blue-50/50 border-r-4 border-r-blue-600' : ''}`}
                            >
                                <div className="flex flex-col gap-1">
                                    <span className="text-xs font-bold text-slate-900">Sample #{r.sample_index + 1}</span>
                                    <span className="text-[10px] text-slate-500 line-clamp-1">{r.original_text}</span>
                                </div>
                                <div className="flex gap-2">
                                    {r.adversarial_success ? <AlertCircle className="w-4 h-4 text-red-500" /> : <CheckCircle2 className="w-4 h-4 text-green-500" />}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Detail View */}
                <div className="lg:col-span-8 space-y-6">
                    {results.results[expandedIndex] && (
                        <>
                            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm transition-all animate-fadeIn">
                                <div className="flex justify-between items-start mb-6">
                                    <h2 className="text-xl font-bold text-slate-900">Pipeline Execution: Sample #{expandedIndex + 1}</h2>
                                    <div className="flex gap-2">
                                        <div className="px-3 py-1 bg-slate-100 rounded-full text-[10px] font-bold text-slate-600">UTILITY: {results.results[expandedIndex].utility_score}</div>
                                        <div className={`px-3 py-1 rounded-full text-[10px] font-bold ${results.results[expandedIndex].adversarial_success ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                                            {results.results[expandedIndex].adversarial_success ? 'RE-ID LEAK' : 'SECURE'}
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <div>
                                        <div className="flex items-center gap-2 mb-3 text-slate-400">
                                            <FileText className="w-4 h-4" />
                                            <span className="text-[10px] font-bold uppercase tracking-widest">Original Data (Ground Truth)</span>
                                        </div>
                                        <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">{results.results[expandedIndex].original_text}</p>
                                    </div>

                                    <div>
                                        <div className="flex items-center gap-2 mb-3 text-blue-500">
                                            <Shield className="w-4 h-4" />
                                            <span className="text-[10px] font-bold uppercase tracking-widest">MaskingAgent Output (Protected)</span>
                                        </div>
                                        <p className="text-sm text-slate-800 leading-relaxed bg-blue-50/30 p-4 rounded-xl border border-blue-100 font-medium">{results.results[expandedIndex].masked_text}</p>
                                    </div>
                                    
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-slate-50 p-4 rounded-xl border">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Scanner Performance</p>
                                            <div className="flex justify-between items-end">
                                                <div>
                                                    <span className="text-2xl font-bold text-slate-800">{(results.results[expandedIndex].f1_score * 100).toFixed(0)}%</span>
                                                    <span className="text-[10px] text-slate-400 ml-1">F1 Score</span>
                                                </div>
                                                <div className="text-right">
                                                    <span className="text-xs font-semibold text-slate-600">{results.results[expandedIndex].detected_count}/{results.results[expandedIndex].ground_truth_count}</span>
                                                    <p className="text-[10px] text-slate-400">PII Caught</p>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="bg-slate-50 p-4 rounded-xl border">
                                            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Strategy Breakdown</p>
                                            <div className="flex flex-wrap gap-1">
                                                {results.results[expandedIndex].strategy_used.slice(0, 4).map((s, i) => (
                                                    <span key={i} className="px-1.5 py-0.5 bg-white border text-[10px] rounded text-slate-500">{s.strategy}</span>
                                                ))}
                                                {results.results[expandedIndex].strategy_used.length > 4 && <span className="text-[10px] text-slate-400 mt-1">+{results.results[expandedIndex].strategy_used.length - 4} more</span>}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* LaTeX Card */}
                            <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800 shadow-xl overflow-hidden relative">
                                <div className="absolute top-0 right-0 p-4">
                                    <button className="text-slate-500 hover:text-white p-2 transition-colors">
                                        <Copy className="w-5 h-5" />
                                    </button>
                                </div>
                                <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-4">LaTeX Publication Table</h3>
                                <pre className="text-[11px] text-slate-300 font-mono leading-relaxed overflow-x-auto whitespace-pre">
                                    {results.aggregate_metrics.latex_table}
                                </pre>
                            </div>
                        </>
                    )}
                </div>
            </div>
        ) : (
            <div className="h-[600px] border-2 border-dashed border-slate-200 rounded-3xl flex flex-col items-center justify-center text-center p-12">
                <div className="w-24 h-24 bg-white rounded-3xl shadow-xl flex items-center justify-center mb-8 rotate-3 border border-slate-100">
                    <FlaskConical className="w-12 h-12 text-blue-600" />
                </div>
                <h2 className="text-2xl font-bold text-slate-800 mb-4">Pipeline Benchmarking</h2>
                <p className="text-slate-500 max-w-md mx-auto leading-relaxed">
                    This module generates synthetic patient records, assembles a ground truth dataset, and runs the full multi-agent anonymization and attack pipeline to compute rigorous research metrics.
                </p>
                
                <div className="mt-12 flex gap-8">
                    {[
                        { label: 'Synthetic Generation', icon: ChevronRight },
                        { label: 'Multi-Agent Flow', icon: ChevronRight },
                        { label: 'Adversarial Attacks', icon: ChevronRight },
                        { label: 'Scientific Output', icon: ChevronRight },
                    ].map((step, i) => (
                        <div key={i} className="flex items-center gap-2 group">
                            <span className="text-[10px] font-black text-slate-300 group-hover:text-blue-500 transition-colors uppercase tracking-widest">{step.label}</span>
                            {i < 3 && <step.icon className="w-3 h-3 text-slate-200" />}
                        </div>
                    ))}
                </div>
            </div>
        )}
      </div>
    </div>
  );
};

export default ExperimentPage;
