import React from 'react';
import { TrendingUp, TrendingDown, Target } from 'lucide-react';

/**
 * MetricsCard
 * value    — numeric 0–1 or null (shows N/A)
 * target   — numeric 0–1 threshold
 * inverse  — true means lower is better (e.g. FNR, Inference Risk)
 */
const MetricsCard = ({ title, value, target, inverse = false }) => {
  const isNull = value === null || value === undefined;
  const diff = (!isNull && target != null) ? (value - target) : 0;
  // For inverse metrics: good when value ≤ target. For normal: good when value ≥ target.
  const isGood = isNull ? false : (inverse ? value <= target : value >= target);
  const barWidth = isNull ? 0 : Math.min(value * 100, 100);

  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm transition-all hover:shadow-md hover:border-blue-100 group">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest group-hover:text-slate-600">{title}</h3>
        <div className={`p-1.5 rounded-lg ${
          isNull ? 'bg-slate-50 text-slate-400'
          : isGood ? 'bg-green-50 text-green-600'
          : 'bg-amber-50 text-amber-600'
        }`}>
          <Target className="w-3 h-3" />
        </div>
      </div>

      <div className="flex items-end gap-2">
        <span className="text-3xl font-black text-slate-900 tracking-tighter">
          {isNull ? 'N/A' : (value * 100).toFixed(1) + '%'}
        </span>
        {!isNull && target != null && (
          <div className={`flex items-center text-[10px] font-bold mb-1 ${isGood ? 'text-green-600' : 'text-amber-600'}`}>
            {isGood ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
            {diff >= 0 ? '+' : ''}{(diff * 100).toFixed(1)}% vs target
          </div>
        )}
        {isNull && <span className="text-[10px] font-bold text-slate-400 mb-1">Not measured</span>}
      </div>

      {target != null && (
        <div className="mt-4 w-full bg-slate-100 h-1 rounded-full overflow-hidden relative">
          <div className="bg-slate-200 h-full w-full absolute top-0 left-0"></div>
          <div
            className={`h-full relative transition-all duration-1000 ${isNull ? 'bg-slate-300' : isGood ? 'bg-green-500' : 'bg-amber-500'}`}
            style={{ width: `${barWidth}%` }}
          ></div>
        </div>
      )}
    </div>
  );
};

export default MetricsCard;
