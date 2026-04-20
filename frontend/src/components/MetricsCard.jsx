import React from 'react';
import { TrendingUp, TrendingDown, Target } from 'lucide-react';

const MetricsCard = ({ title, value, target, inverse = false }) => {
  const diff = target ? (value - target) : 0;
  const isGood = inverse ? value <= target : value >= target;
  
  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm transition-all hover:shadow-md hover:border-blue-100 group">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest group-hover:text-slate-600">{title}</h3>
        <div className={`p-1.5 rounded-lg ${isGood ? 'bg-green-50 text-green-600' : 'bg-amber-50 text-amber-600'}`}>
          <Target className="w-3 h-3" />
        </div>
      </div>
      
      <div className="flex items-end gap-2">
        <span className="text-3xl font-black text-slate-900 tracking-tighter">
            {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : value}
        </span>
        {target && (
            <div className={`flex items-center text-[10px] font-bold mb-1 ${isGood ? 'text-green-600' : 'text-amber-600'}`}>
                {isGood ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
                {diff >= 0 ? '+' : ''}{(diff * 100).toFixed(1)}% vs target
            </div>
        )}
      </div>
      
      {target && (
          <div className="mt-4 w-full bg-slate-100 h-1 rounded-full overflow-hidden relative">
             <div className="bg-slate-200 h-full w-full absolute top-0 left-0"></div>
             <div 
                className={`h-full relative transition-all duration-1000 ${isGood ? 'bg-green-500' : 'bg-amber-500'}`} 
                style={{ width: `${value * 100}%` }}
             ></div>
          </div>
      )}
    </div>
  );
};

export default MetricsCard;
