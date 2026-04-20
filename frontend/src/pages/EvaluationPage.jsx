import React, { useState } from 'react';
import { Play, Loader2, BarChart2, Shield, CheckCircle2, AlertCircle, FileText } from 'lucide-react';
import MetricsCard from '../components/MetricsCard';
import { useDocSentry } from '../context/DocSentryContext';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const STEPS = [
  { id: 'pii',     label: 'PII Detection' },
  { id: 'anon',    label: 'Anonymization Quality' },
  { id: 'overall', label: '9-Parameter Snapshot' },
];

const EvaluationPage = () => {
  const {
    currentDocText,
    evalResults,    setEvalResults,
    piiText,        setPiiText,
    anonResults,    setAnonResults,
    overallResults, setOverallResults,
  } = useDocSentry();

  const [isRunning, setIsRunning]   = useState(false);
  const [activeStep, setActiveStep] = useState(null); // null | 'pii' | 'anon' | 'overall' | 'done'
  const [error, setError]           = useState('');

  const loadCurrentDoc = () => {
    if (currentDocText) setPiiText(currentDocText);
  };

  const runFullEvaluation = async () => {
    if (!piiText.trim()) return;
    setIsRunning(true);
    setError('');
    setEvalResults(null);
    setAnonResults(null);
    setOverallResults(null);

    try {
      // ── Step 1: PII Detection ─────────────────────────────────────────────
      setActiveStep('pii');
      const piiRes  = await fetch(`${API_URL}/evaluate/pii_detection`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ original_text: piiText, ground_truth_pii: [] }),
      });
      const piiData = await piiRes.json();
      if (piiData.detail) throw new Error(`PII step: ${piiData.detail}`);
      setEvalResults(piiData);

      // ── Step 2: Anonymization Quality ─────────────────────────────────────
      setActiveStep('anon');
      const anonRes  = await fetch(`${API_URL}/evaluate/anonymization`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          original_text:   piiText,
          anonymized_text: piiData.anonymized_text || piiText,
        }),
      });
      const anonData = await anonRes.json();
      if (anonData.detail) throw new Error(`Anon step: ${anonData.detail}`);
      setAnonResults(anonData);

      // ── Step 3: Overall 9-parameter scan ─────────────────────────────────
      setActiveStep('overall');
      const overallRes  = await fetch(`${API_URL}/evaluate/overall_system`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ original_text: piiText, ground_truth_pii: [] }),
      });
      const overallData = await overallRes.json();
      if (overallData.detail) throw new Error(`Overall step: ${overallData.detail}`);
      setOverallResults(overallData);

    } catch (e) {
      console.error(e);
      setError(e.message || 'Evaluation failed. Check the backend terminal.');
    }

    setActiveStep('done');
    setIsRunning(false);
  };

  const stepIndex = STEPS.findIndex(s => s.id === activeStep);

  return (
    <div className="flex flex-col h-full bg-slate-50 p-8 overflow-y-auto">
      <div className="max-w-5xl mx-auto w-full space-y-8">

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <header>
          <h1 className="text-3xl font-bold text-slate-900">Evaluation Dashboard</h1>
          <p className="text-slate-500 mt-1 text-sm">All 9 research metrics in a single automated scan.</p>
        </header>

        {/* ── Input + Run button ─────────────────────────────────────────── */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-3">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">
              Document Text
            </label>
            {currentDocText && (
              <button
                onClick={loadCurrentDoc}
                className="text-[10px] font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 bg-blue-50 px-2 py-1 rounded"
              >
                <FileText className="w-3 h-3" /> Import Current Doc
              </button>
            )}
          </div>

          <textarea
            value={piiText}
            onChange={e => setPiiText(e.target.value)}
            placeholder="Paste medical record text here, or click Import Current Doc above..."
            className="w-full h-36 p-4 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-sm resize-none transition-all"
          />

          {/* Progress indicator */}
          {isRunning && (
            <div className="mt-4 space-y-2">
              <div className="flex gap-6">
                {STEPS.map((s, i) => (
                  <div
                    key={s.id}
                    className={`flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest transition-colors ${
                      i < stepIndex ? 'text-green-600' : i === stepIndex ? 'text-blue-600' : 'text-slate-300'
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${
                      i < stepIndex  ? 'bg-green-500'
                      : i === stepIndex ? 'bg-blue-500 animate-pulse'
                      : 'bg-slate-200'
                    }`} />
                    {s.label}
                  </div>
                ))}
              </div>
              <div className="h-1 w-full bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-700"
                  style={{ width: `${Math.max(5, ((stepIndex + 1) / STEPS.length) * 100)}%` }}
                />
              </div>
            </div>
          )}

          {error && (
            <div className="mt-3 p-3 bg-rose-50 border border-rose-100 rounded-xl text-xs text-rose-700 font-medium">
              ⚠ {error}
            </div>
          )}

          <button
            onClick={runFullEvaluation}
            disabled={isRunning || !piiText.trim()}
            className="mt-4 w-full py-4 bg-blue-600 text-white rounded-2xl font-bold hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-all shadow-lg flex items-center justify-center gap-2"
          >
            {isRunning
              ? <><Loader2 className="w-5 h-5 animate-spin" /> Running evaluation...</>
              : <><Play className="w-5 h-5" /> Run Full Evaluation</>}
          </button>
        </div>

        {/* ── Section 1: PII Detection ───────────────────────────────────── */}
        {evalResults && (
          <section className="space-y-4 animate-fadeIn">
            <SectionTitle icon={<Shield className="w-4 h-4 text-blue-500" />} label="PII Detection" />

            <div className="grid grid-cols-3 gap-4">
              <MetricsCard title="Precision"  value={evalResults.precision}  target={0.95} />
              <MetricsCard title="Recall"     value={evalResults.recall}     target={0.95} />
              <MetricsCard title="F1 Score"   value={evalResults.f1_score}   target={0.95} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Per-category */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Per-Category F1</h3>
                <div className="space-y-2.5">
                  {Object.entries(evalResults.per_category || {}).map(([cat, stats]) => (
                    <div key={cat}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="font-semibold text-slate-700">{cat}</span>
                        <span className="text-slate-500">{(stats.f1 * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-blue-500 h-full rounded-full" style={{ width: `${stats.f1 * 100}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Anonymized output preview */}
              {evalResults.anonymized_text && (
                <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Anonymized Output</h3>
                  <textarea
                    readOnly
                    value={evalResults.anonymized_text}
                    className="flex-1 min-h-[140px] p-3 bg-green-50 text-green-800 font-mono text-xs rounded-xl border border-green-200 outline-none resize-none"
                  />
                </div>
              )}
            </div>
          </section>
        )}

        {/* ── Section 2: Anonymization Quality ──────────────────────────── */}
        {anonResults && (
          <section className="space-y-4 animate-fadeIn">
            <SectionTitle icon={<Shield className="w-4 h-4 text-green-500" />} label="Anonymization Quality" />

            <div className="grid grid-cols-3 gap-4">
              <MetricsCard title="Redaction Coverage"  value={anonResults.redaction_coverage}              target={1.0}  />
              <MetricsCard title="Adversarial Risk"    value={anonResults.adversarial_success_rate || 0}   target={0.05} inverse={true} />
              <MetricsCard title="Utility Score"       value={(anonResults.utility_score || 0) / 100}      target={0.8}  />
            </div>

            <div className={`p-4 rounded-2xl border flex items-start gap-3 ${
              anonResults.pii_leakage_detected ? 'bg-rose-50 border-rose-100' : 'bg-green-50 border-green-100'
            }`}>
              {anonResults.pii_leakage_detected
                ? <AlertCircle  className="w-4 h-4 text-rose-500  shrink-0 mt-0.5" />
                : <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />}
              <div>
                <p className={`text-sm font-bold ${anonResults.pii_leakage_detected ? 'text-rose-700' : 'text-green-700'}`}>
                  {anonResults.pii_leakage_detected
                    ? `PII Leakage Detected — ${anonResults.leaked_entities?.join(', ')}`
                    : 'Zero Leakage — All detected PII replaced successfully'}
                </p>
                {anonResults.fidelity_rating && (
                  <p className="text-xs text-slate-500 mt-1 italic">"{anonResults.fidelity_rating}"</p>
                )}
              </div>
            </div>
          </section>
        )}

        {/* ── Section 3: 9-Parameter System Snapshot ────────────────────── */}
        {overallResults && (
          <section className="space-y-4 animate-fadeIn">
            <SectionTitle icon={<BarChart2 className="w-4 h-4 text-indigo-500" />} label="9-Parameter System Snapshot" />

            <div className="grid grid-cols-3 gap-4">
              <MetricsCard title="1. PII F1-Score"         value={overallResults.pii_detection_f1}          target={0.95} />
              <MetricsCard title="2. Redaction Coverage"   value={overallResults.redaction_coverage}        target={1.0}  />
              <MetricsCard title="3. Inference Risk"       value={overallResults.inference_risk}            target={0.05} inverse={true} />
              <MetricsCard title="4. Retrieval Accuracy"   value={overallResults.retrieval_accuracy ?? null} target={0.8}  />
              <MetricsCard title="5. LLM Response Quality" value={overallResults.llm_response_quality}      target={0.8}  />
              <MetricsCard title="6. E2E Leakage Rate"     value={overallResults.end_to_end_leakage_rate}   target={0.05} inverse={true} />
              <MetricsCard title="7. Query Accuracy"       value={overallResults.query_accuracy}            target={0.8}  />
              <MetricsCard title="8. Over-Detection Rate"  value={overallResults.over_detection_rate}       target={0.1}  inverse={true} />
              <MetricsCard title="9. False Negative Rate"  value={overallResults.false_negative_rate}       target={0.05} inverse={true} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <MetricsCard title="Privacy Score (Composite)" value={overallResults.privacy_score}            target={0.85} />
              <MetricsCard title="Utility Score (Composite)" value={overallResults.composite_utility_score}  target={0.7}  />
            </div>
          </section>
        )}

        {/* Empty state */}
        {!evalResults && !isRunning && (
          <div className="h-64 border-2 border-dashed border-slate-200 rounded-3xl flex flex-col items-center justify-center text-center p-8 text-slate-400">
            <BarChart2 className="w-10 h-10 mb-3 opacity-20" />
            <p className="text-sm font-medium">Paste document text above and click Run Full Evaluation</p>
            <p className="text-xs mt-1 opacity-70">All 9 metrics will appear here as each step completes</p>
          </div>
        )}

      </div>
    </div>
  );
};

// ── Small helper component ──────────────────────────────────────────────────
const SectionTitle = ({ icon, label }) => (
  <h2 className="text-sm font-black text-slate-500 uppercase tracking-widest flex items-center gap-2 border-b border-slate-200 pb-3">
    {icon} {label}
  </h2>
);

export default EvaluationPage;
