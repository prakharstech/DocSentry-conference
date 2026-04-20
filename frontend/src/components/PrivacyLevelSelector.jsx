import React from 'react';
import { FlaskConical, Tag, ShieldOff } from 'lucide-react';

/**
 * PrivacyLevelSelector
 *
 * Lets the user choose one of three privacy modes before uploading a document:
 *  - SYNTHETIC  : PII replaced with realistic fake data (highest utility)
 *  - GENERALIZE : PII replaced with [PERSON], [DATE] tags (balanced)
 *  - REDACT     : PII replaced with [REDACTED] (maximum privacy)
 */

const LEVELS = [
  {
    id: 'SYNTHETIC',
    label: 'Synthetic',
    icon: FlaskConical,
    tagline: 'Realistic Fakes',
    description: 'Names, dates and SSNs are swapped with believable synthetic data. Documents remain fully readable.',
    privacyDots: 2,
    utilityDots: 3,
    color: 'emerald',
    bgClass: 'bg-emerald-50 border-emerald-200',
    activeBg: 'bg-emerald-600 text-white border-emerald-700',
    iconBg: 'bg-emerald-100 text-emerald-600',
    activeIconBg: 'bg-emerald-500 text-white',
    dotActive: 'bg-emerald-500',
    dotInactive: 'bg-emerald-200',
  },
  {
    id: 'GENERALIZE',
    label: 'Generalize',
    icon: Tag,
    tagline: 'Category Tags',
    description: 'PII is replaced with type labels like [PERSON] and [SSN]. Context is preserved but identity is hidden.',
    privacyDots: 3,
    utilityDots: 2,
    color: 'amber',
    bgClass: 'bg-amber-50 border-amber-200',
    activeBg: 'bg-amber-500 text-white border-amber-600',
    iconBg: 'bg-amber-100 text-amber-600',
    activeIconBg: 'bg-amber-400 text-white',
    dotActive: 'bg-amber-500',
    dotInactive: 'bg-amber-200',
  },
  {
    id: 'REDACT',
    label: 'Full Redact',
    icon: ShieldOff,
    tagline: 'Maximum Privacy',
    description: 'Everything sensitive becomes [REDACTED]. No information about PII type or value is kept.',
    privacyDots: 4,
    utilityDots: 1,
    color: 'rose',
    bgClass: 'bg-rose-50 border-rose-200',
    activeBg: 'bg-rose-600 text-white border-rose-700',
    iconBg: 'bg-rose-100 text-rose-600',
    activeIconBg: 'bg-rose-500 text-white',
    dotActive: 'bg-rose-500',
    dotInactive: 'bg-rose-200',
  },
];

const DotRating = ({ filled, total, activeClass, inactiveClass }) => (
  <div className="flex gap-1">
    {Array.from({ length: total }).map((_, i) => (
      <span
        key={i}
        className={`w-2 h-2 rounded-full ${i < filled ? activeClass : inactiveClass}`}
      />
    ))}
  </div>
);

const PrivacyLevelSelector = ({ selected, onChange, disabled }) => {
  return (
    <div className="space-y-2">
      <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest block mb-3">
        Privacy Level
      </label>
      <div className="space-y-2">
        {LEVELS.map((level) => {
          const Icon = level.icon;
          const isActive = selected === level.id;

          return (
            <button
              key={level.id}
              id={`privacy-level-${level.id.toLowerCase()}`}
              onClick={() => !disabled && onChange(level.id)}
              disabled={disabled}
              className={`
                w-full text-left p-3 rounded-2xl border-2 transition-all duration-200
                ${isActive
                  ? level.activeBg + ' shadow-lg'
                  : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm'}
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className={`
                  w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5
                  ${isActive ? level.activeIconBg : level.iconBg}
                `}>
                  <Icon className="w-4 h-4" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className={`text-xs font-black ${isActive ? 'text-white' : 'text-slate-800'}`}>
                      {level.label}
                    </span>
                    <span className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                      isActive
                        ? 'bg-white/20 text-white'
                        : 'bg-slate-100 text-slate-500'
                    }`}>
                      {level.tagline}
                    </span>
                  </div>

                  <p className={`text-[9px] leading-relaxed mb-2 ${isActive ? 'text-white/80' : 'text-slate-500'}`}>
                    {level.description}
                  </p>

                  {/* Privacy / Utility rating dots */}
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[8px] font-bold ${isActive ? 'text-white/60' : 'text-slate-400'}`}>
                        Privacy
                      </span>
                      <DotRating
                        filled={level.privacyDots}
                        total={4}
                        activeClass={isActive ? 'bg-white' : level.dotActive}
                        inactiveClass={isActive ? 'bg-white/25' : level.dotInactive}
                      />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className={`text-[8px] font-bold ${isActive ? 'text-white/60' : 'text-slate-400'}`}>
                        Utility
                      </span>
                      <DotRating
                        filled={level.utilityDots}
                        total={3}
                        activeClass={isActive ? 'bg-white' : level.dotActive}
                        inactiveClass={isActive ? 'bg-white/25' : level.dotInactive}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Helper note */}
      <p className="text-[8px] text-slate-400 italic leading-snug pt-1">
        Privacy level is applied at upload time and cannot be changed after processing.
      </p>
    </div>
  );
};

export default PrivacyLevelSelector;
