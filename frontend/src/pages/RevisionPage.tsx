import React, { useState } from 'react';
import { CheckCircle2, RotateCcw, Sparkles, TrendingUp, AlertTriangle } from 'lucide-react';

export const RevisionPage: React.FC = () => {
  const [revisionItems, setRevisionItems] = useState([
    { concept: 'Partial Derivatives', subject: 'Machine Learning', retention: '38%', interval: 1, ease: 2.36, due: 'Today' },
    { concept: 'Backpropagation Algorithm', subject: 'Neural Networks', retention: '52%', interval: 6, ease: 2.50, due: 'Tomorrow' },
    { concept: 'Consensus Protocols', subject: 'Distributed Systems', retention: '85%', interval: 14, ease: 2.65, due: 'In 5 days' },
  ]);

  const [completedList, setCompletedList] = useState<string[]>([]);

  const handleGradeQuality = (concept: string, grade: number) => {
    setCompletedList([...completedList, concept]);
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">SuperMemo SM-2 Spaced Repetition</h2>
        <p className="text-xs text-[#9CA3AF] mt-1">
          Review concepts scheduled by the SuperMemo SM-2 algorithm to prevent Ebbinghaus memory decay and lock in long-term retention.
        </p>
      </div>

      {/* Revision Queue */}
      <div className="space-y-4">
        {revisionItems.map((item) => {
          const isDone = completedList.includes(item.concept);

          return (
            <div key={item.concept} className={`glass-card p-6 rounded-2xl border transition-all ${
              isDone ? 'border-[#10B981]/40 opacity-60' : 'border-[#232D3F]'
            }`}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20">
                      {item.subject}
                    </span>
                    <span className="text-[10px] text-amber-400 font-semibold flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Due {item.due}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-white">{item.concept}</h3>
                  <div className="mt-2 flex items-center gap-4 text-xs text-[#9CA3AF]">
                    <span>Retention R(t): <strong className="text-white">{item.retention}</strong></span>
                    <span>Ease Factor: <strong className="text-white">{item.ease}</strong></span>
                    <span>Interval: <strong className="text-white">{item.interval} days</strong></span>
                  </div>
                </div>

                {!isDone ? (
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[10px] text-[#9CA3AF] block w-full sm:w-auto mb-1 sm:mb-0">Rate Recall:</span>
                    {[
                      { grade: 0, label: '0 Blackout', color: 'bg-red-500/20 text-red-400 hover:bg-red-500/40' },
                      { grade: 3, label: '3 Passable', color: 'bg-amber-500/20 text-amber-400 hover:bg-amber-500/40' },
                      { grade: 5, label: '5 Perfect', color: 'bg-[#10B981]/20 text-[#10B981] hover:bg-[#10B981]/40' },
                    ].map((g) => (
                      <button
                        key={g.grade}
                        onClick={() => handleGradeQuality(item.concept, g.grade)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${g.color}`}
                      >
                        {g.label}
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-xs font-bold text-[#10B981]">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>SM-2 Schedule Recalibrated!</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
