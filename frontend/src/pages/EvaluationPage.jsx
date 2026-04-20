import React, { useState } from 'react';
import { Play, Loader2, BarChart2, Shield, Search, CheckCircle2, AlertCircle, FileText, Download, Table } from 'lucide-react';
import MetricsCard from '../components/MetricsCard';
import { useDocSentry } from '../context/DocSentryContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const EvaluationPage = () => {
    const { 
        currentDocText, currentDocFindings, 
        evalResults, setEvalResults,
        piiText, setPiiText,
        groundTruthJson, setGroundTruthJson,
        anonResults, setAnonResults,
        ragResults, setRagResults,
        overallResults, setOverallResults
    } = useDocSentry();

    const [activeTab, setActiveTab] = useState('pii');
    const [isLoading, setIsLoading] = useState(false);

    const loadCurrentDoc = () => {
        if (currentDocText) {
            setPiiText(currentDocText);
            // For ground truth in a benchmark, we usually need human labels.
            // But we can show the user how to format their ground truth based on what was found.
            const mockGT = currentDocFindings.map(f => ({
                text: f.text_segment,
                type: f.pii_type
            }));
            setGroundTruthJson(JSON.stringify(mockGT, null, 2));
        }
    };

    const runPIIEval = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${API_URL}/evaluate/pii_detection`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    original_text: piiText,
                    ground_truth_pii: JSON.parse(groundTruthJson)
                })
            });
            const data = await response.json();
            setEvalResults(data);
        } catch (e) {
            console.error(e);
            alert('PII Evaluation failed. Check console and JSON format.');
        }
        setIsLoading(false);
    };

    const runAnonEval = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${API_URL}/evaluate/anonymization`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    original_text: piiText,
                    anonymized_text: evalResults?.anonymized_text || piiText,
                    // Do NOT send detected_pii here — backend auto-scans from original_text
                })
            });
            const data = await response.json();
            if (data.detail) throw new Error(data.detail);
            setAnonResults(data);
        } catch (e) {
            console.error(e);
            alert('Anonymization Evaluation failed: ' + e.message);
        }
        setIsLoading(false);
    };

    const runRAGEval = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${API_URL}/evaluate/rag_response`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: "What is this document about?",
                    response: "This document contains sensitive information.",
                    expected_answer: "The document relates to sensitive data analysis.",
                    context_chunks: [piiText || "Sample context snippet."],
                    ground_truth_chunk_indices: [0]
                })
            });
            const data = await response.json();
            setRagResults(data);
        } catch (e) {
            console.error(e);
            alert('RAG Evaluation failed. Check console and JSON format.');
        }
        setIsLoading(false);
    };

    return (
        <div className="flex flex-col h-full bg-slate-50 p-8 overflow-y-auto">
            <div className="max-w-6xl mx-auto w-full">
                <header className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900">Evaluation Dashboard</h1>
                    <p className="text-slate-500 mt-2">Rigorous scientific verification of PII detection and RAG quality.</p>
                </header>

                {/* Tabs */}
                <div className="flex gap-8 border-b border-slate-200 mb-8">
                    {['pii', 'anonymization', 'rag', 'overall'].map(tab => (
                        <button
                            key={tab}
                            onClick={() => { setActiveTab(tab); }}
                            className={`pb-4 text-sm font-semibold transition-all ${activeTab === tab ? 'border-b-2 border-blue-600 text-blue-600' : 'text-slate-400 hover:text-slate-600'}`}
                        >
                            {tab.toUpperCase()} {tab === 'overall' ? 'STRENGTH' : 'VALIDATION'}
                        </button>
                    ))}
                </div>

            {activeTab === 'pii' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <div className="lg:col-span-2 space-y-6">
                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                            <div className="flex justify-between items-center mb-4">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Input Text (Unstructured)</label>
                                {currentDocText && (
                                    <button
                                        onClick={loadCurrentDoc}
                                        className="text-[10px] font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 bg-blue-50 px-2 py-1 rounded"
                                    >
                                        <FileText className="w-3 h-3" />
                                        Import Current Doc
                                    </button>
                                )}
                            </div>
                            <textarea
                                value={piiText}
                                onChange={(e) => setPiiText(e.target.value)}
                                placeholder="Paste text with PII here..."
                                className="w-full h-40 p-4 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all text-sm"
                            />
                        </div>
                        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                            <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Ground Truth (JSON Array)</label>
                            <textarea
                                value={groundTruthJson}
                                onChange={(e) => setGroundTruthJson(e.target.value)}
                                className="w-full h-32 p-4 bg-slate-950 text-blue-400 font-mono text-xs rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all mb-4"
                            />
                            
                            {evalResults?.anonymized_text && (
                                <>
                                    <label className="block text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 border-t border-slate-100 pt-4">Anonymized Output</label>
                                    <textarea
                                        readOnly
                                        value={evalResults.anonymized_text}
                                        className="w-full h-24 p-4 bg-green-50 text-green-800 font-mono text-xs rounded-xl border border-green-200 outline-none transition-all resize-none"
                                    />
                                </>
                            )}
                        </div>
                        <button
                            onClick={runPIIEval}
                            disabled={isLoading || !piiText}
                            className="w-full py-4 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 disabled:bg-slate-300 transition-all shadow-lg flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                            Run Detection Benchmark
                        </button>
                    </div>

                    <div className="space-y-6">
                        {evalResults ? (
                            <>
                                <MetricsCard title="Precision" value={evalResults.precision} target={0.95} />
                                <MetricsCard title="Recall" value={evalResults.recall} target={0.95} />
                                <MetricsCard title="F1 Score" value={evalResults.f1_score} target={0.95} />
                                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Per-Category F1</h3>
                                    <div className="space-y-3">
                                        {Object.entries(evalResults.per_category || {}).map(([cat, stats]) => (
                                            <div key={cat} className="flex flex-col gap-1">
                                                <div className="flex justify-between text-xs">
                                                    <span className="font-semibold text-slate-700">{cat}</span>
                                                    <span className="text-slate-500">{(stats.f1 * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                                                    <div className="bg-blue-500 h-full" style={{ width: `${stats.f1 * 100}%` }}></div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="h-full border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center p-8 text-center text-slate-400">
                                <BarChart2 className="w-12 h-12 mb-4 opacity-20" />
                                <p className="text-sm font-medium">Run benchmark to see metrics</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {activeTab === 'anonymization' && (
                <div className="space-y-8 animate-fadeIn">
                    <div className="flex justify-between items-center mb-4">
                        <button
                            onClick={runAnonEval}
                            disabled={isLoading || !piiText}
                            className="w-full lg:w-auto py-4 px-8 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 disabled:bg-slate-300 transition-all shadow-lg flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                            Run Anonymization Benchmark
                        </button>
                    </div>

                    {anonResults ? (
                        <>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                <MetricsCard title="Redaction Coverage" value={anonResults.redaction_coverage || 0.0} target={1.0} />
                                <MetricsCard title="Adversarial Success (Risk)" value={anonResults.adversarial_success_rate || 0.0} target={0.05} inverse={true} />
                                <MetricsCard title="Utility Score" value={(anonResults.utility_score || 0) / 100} target={0.8} />
                            </div>
                            
                            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm">
                                <div className="flex items-center gap-3 mb-6">
                                    <Shield className="w-5 h-5 text-blue-600" />
                                    <h3 className="font-bold text-slate-800">Privacy Leakage Analysis</h3>
                                </div>
                                {anonResults.pii_leakage_detected ? (
                                    <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl flex items-start gap-4">
                                        <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
                                        <div>
                                            <p className="text-sm font-bold text-rose-700">PII Leakage Detected</p>
                                            <p className="text-xs text-rose-600 mt-1">Found original PII strings in anonymized text: {anonResults.leaked_entities?.join(', ')}</p>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="p-4 bg-green-50 border border-green-100 rounded-xl flex items-start gap-4">
                                        <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
                                        <div>
                                            <p className="text-sm font-bold text-green-700">Zero Leakage Detected</p>
                                            <p className="text-xs text-green-600 mt-1">The anonymizer successfully replaced all detected PII strings with placeholders.</p>
                                        </div>
                                    </div>
                                )}
                                <div className="mt-8 pt-8 border-t border-slate-100">
                                     <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Adversarial Agent Reasoning</h4>
                                     <p className="text-sm text-slate-600 leading-relaxed italic">
                                        "{anonResults.fidelity_rating || 'Run evaluation to generate adversarial report.'}"
                                     </p>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="h-40 border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center p-8 text-center text-slate-400">
                            <BarChart2 className="w-12 h-12 mb-4 opacity-20" />
                            <p className="text-sm font-medium">Run benchmark to see metrics</p>
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'rag' && (
                <div className="space-y-8 animate-fadeIn">
                    <div className="flex justify-between items-center mb-4">
                        <button
                            onClick={runRAGEval}
                            disabled={isLoading || !piiText}
                            className="w-full lg:w-auto py-4 px-8 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 disabled:bg-slate-300 transition-all shadow-lg flex items-center justify-center gap-2"
                        >
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                            Run RAG Benchmark
                        </button>
                    </div>

                    {ragResults ? (
                        <>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <MetricsCard title="Answer Relevancy" value={(ragResults.relevancy_score || 0) / 10} target={0.9} />
                                <MetricsCard title="Groundedness" value={(ragResults.groundedness_score || 0) / 10} target={0.9} />
                                <MetricsCard title="Context Precision" value={ragResults.context_precision || 0.0} target={0.8} />
                                <MetricsCard title="Context Recall" value={ragResults.context_recall || 0.0} target={0.8} />
                            </div>
                            
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                                    <h3 className="text-sm font-bold text-slate-800 mb-4">Relevancy Critique</h3>
                                    <p className="text-sm text-slate-600 leading-relaxed">{ragResults.relevancy_reasoning || 'No evaluation run.'}</p>
                                </div>
                                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                                    <h3 className="text-sm font-bold text-slate-800 mb-4">Groundedness Critique</h3>
                                    <p className="text-sm text-slate-600 leading-relaxed">{ragResults.groundedness_reasoning || 'No evaluation run.'}</p>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="h-40 border-2 border-dashed border-slate-200 rounded-2xl flex flex-col items-center justify-center p-8 text-center text-slate-400">
                            <BarChart2 className="w-12 h-12 mb-4 opacity-20" />
                            <p className="text-sm font-medium">Run benchmark to see metrics</p>
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'overall' && (
                <div className="space-y-8 animate-fadeIn">
                    <div className="flex justify-between items-center bg-blue-600 p-8 rounded-3xl text-white shadow-xl shadow-blue-100">
                        <div>
                            <h2 className="text-2xl font-black mb-2">Phase 3 System Snapshot</h2>
                            <p className="opacity-80 text-sm max-w-lg">Comprehensive view of all 9 parameters governing PII protection and RAG agent effectiveness.</p>
                        </div>
                        <button 
                            onClick={async () => {
                                setIsLoading(true);
                                const res = await fetch(`${API_URL}/evaluate/overall_system`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        original_text: piiText,
                                        ground_truth_pii: JSON.parse(groundTruthJson)
                                    })
                                });
                                const data = await res.json();
                                setOverallResults(data);
                                setIsLoading(false);
                            }}
                            className="px-8 py-4 bg-white text-blue-600 rounded-2xl font-black uppercase tracking-wider hover:bg-blue-50 transition-all shadow-lg flex items-center gap-3"
                        >
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
                            Execute Holistic Scan
                        </button>
                    </div>

                    {overallResults && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                            <MetricsCard title="1. PII F1-Score" value={overallResults.pii_detection_f1} target={0.95} />
                            <MetricsCard title="2. Redaction Coverage" value={overallResults.redaction_coverage} target={1.0} />
                            <MetricsCard title="3. Inference Risk" value={overallResults.inference_risk} target={0.05} inverse={true} />
                            <MetricsCard title="4. Retrieval Accuracy" value={overallResults.retrieval_accuracy ?? null} target={0.8} />
                            <MetricsCard title="5. LLM Response Quality" value={overallResults.llm_response_quality} target={0.8} />
                            <MetricsCard title="6. E2E Leakage Rate" value={overallResults.end_to_end_leakage_rate} target={0.05} inverse={true} />
                            <MetricsCard title="7. Query Accuracy" value={overallResults.query_accuracy} target={0.8} />
                            <MetricsCard title="8. Over-Detection Rate" value={overallResults.over_detection_rate} target={0.1} inverse={true} />
                            <MetricsCard title="9. False Negative Rate" value={overallResults.false_negative_rate} target={0.05} inverse={true} />
                            <MetricsCard title="Privacy Score" value={overallResults.privacy_score} target={0.85} />
                            <MetricsCard title="Utility Score" value={overallResults.composite_utility_score} target={0.7} />
                        </div>
                    )}
                </div>
            )}
        </div>
    </div >
  );
};

export default EvaluationPage;
