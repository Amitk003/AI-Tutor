import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  Flame,
  Clock,
  BookOpen,
  Brain,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  Plus,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';
import { useStudyStore } from '../store/useStudyStore';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { startSession } = useStudyStore();

  const [profileData, setProfileData] = useState<any>(null);
  const [learningState, setLearningState] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      setIsLoading(true);
      try {
        const [profRes, stateRes, recRes] = await Promise.all([
          apiClient.get('/student/profile'),
          apiClient.get('/student/state'),
          apiClient.get('/student/recommendations?current_topic=Binary Search Tree'),
        ]);

        setProfileData(profRes.data);
        setLearningState(stateRes.data);
        setRecommendations(recRes.data);
      } catch (err) {
        console.warn('Dashboard load fallback:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  const handleLaunchQuickSession = (concept: string) => {
    const newSessionId = crypto.randomUUID();
    startSession(newSessionId, concept);
    navigate('/study');
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-32 bg-[#161B26] rounded-2xl border border-[#232D3F]" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-[#161B26] rounded-xl border border-[#232D3F]" />
          ))}
        </div>
      </div>
    );
  }

  const streakDays = profileData?.learning_streak_days || 4;
  const abilityTheta = learningState?.ability_theta || 0.50;
  const currentFocus = learningState?.current_focus_topic || 'Binary Search Tree';
  const revisionQueue = recommendations?.revision_recommendations || [];

  return (
    <div className="space-y-8">
      {/* Top Banner & Learning Streak Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-[#161B26] via-[#1E2536] to-[#161B26] border border-[#232D3F] p-6 md:p-8">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#6366F1]/10 border border-[#6366F1]/20 text-[#6366F1] text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5" /> Welcome Back, {user?.full_name || 'Student'}
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              Ready to Study <span className="text-[#6366F1]">{currentFocus}</span>?
            </h2>
            <p className="text-xs text-[#9CA3AF] mt-1 max-w-xl">
              Your AI Companion has analyzed your uploaded notes and prepared personalized Socratic explanations tailored to your IRT ability ($\theta = {abilityTheta.toFixed(2)}$).
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-[#0B0F17]/80 border border-[#232D3F]">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
                <Flame className="w-5 h-5 fill-amber-500" />
              </div>
              <div>
                <span className="text-xs text-[#9CA3AF] block">Daily Streak</span>
                <span className="text-base font-bold text-white">{streakDays} Days</span>
              </div>
            </div>

            <button
              onClick={() => handleLaunchQuickSession(currentFocus)}
              className="px-5 py-3 rounded-xl bg-[#6366F1] hover:bg-[#6366F1]/90 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-[#6366F1]/25 transition-all whitespace-nowrap"
            >
              <span>Resume Study Session</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* SM-2 Memory Decay Revision Alert Banner */}
      {revisionQueue.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
            <div>
              <h3 className="text-xs font-bold text-amber-400">SuperMemo SM-2 Revision Due Today</h3>
              <p className="text-[11px] text-[#9CA3AF]">
                Concept <span className="font-semibold text-white">{revisionQueue[0]?.concept_name}</span> is experiencing Ebbinghaus memory decay. Review today to maintain long-term retention.
              </p>
            </div>
          </div>
          <button
            onClick={() => navigate('/revision')}
            className="px-3.5 py-1.5 rounded-lg bg-amber-500 text-black text-xs font-bold hover:bg-amber-400 transition-colors whitespace-nowrap"
          >
            Review Now
          </button>
        </div>
      )}

      {/* Mastery Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-5 rounded-xl border border-[#232D3F]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#9CA3AF]">IRT Latent Ability (θ)</span>
            <Brain className="w-4 h-4 text-[#6366F1]" />
          </div>
          <span className="text-2xl font-bold text-white">{abilityTheta.toFixed(2)}</span>
          <span className="text-[10px] text-[#10B981] block mt-1">Standard Psychometric Scale [-3, +3]</span>
        </div>

        <div className="glass-card p-5 rounded-xl border border-[#232D3F]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#9CA3AF]">BKT Mastery P(L)</span>
            <TrendingUp className="w-4 h-4 text-[#10B981]" />
          </div>
          <span className="text-2xl font-bold text-white">78%</span>
          <span className="text-[10px] text-[#9CA3AF] block mt-1">Across 12 Active Concepts</span>
        </div>

        <div className="glass-card p-5 rounded-xl border border-[#232D3F]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#9CA3AF]">Total Study Time</span>
            <Clock className="w-4 h-4 text-[#8B5CF6]" />
          </div>
          <span className="text-2xl font-bold text-white">14.2 hrs</span>
          <span className="text-[10px] text-[#9CA3AF] block mt-1">This Month</span>
        </div>

        <div className="glass-card p-5 rounded-xl border border-[#232D3F]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-[#9CA3AF]">Uploaded Notes</span>
            <BookOpen className="w-4 h-4 text-amber-400" />
          </div>
          <span className="text-2xl font-bold text-white">8 Files</span>
          <span className="text-[10px] text-[#9CA3AF] block mt-1">PDF, DOCX, PPTX Parsed</span>
        </div>
      </div>

      {/* Enrolled Subject Workspaces */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white">Subject Workspaces</h3>
          <button
            onClick={() => navigate('/subjects')}
            className="text-xs text-[#6366F1] font-semibold hover:underline flex items-center gap-1"
          >
            <Plus className="w-3.5 h-3.5" /> Upload Material
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { id: 'cs101', name: 'Data Structures & Algorithms', files: 4, mastery: '82%', topic: 'Binary Search Tree' },
            { id: 'ml201', name: 'Machine Learning & AI Principles', files: 3, mastery: '65%', topic: 'Gradient Descent' },
            { id: 'sys301', name: 'Distributed Systems & Databases', files: 2, mastery: '70%', topic: 'Consensus Algorithms' },
          ].map((subject) => (
            <div
              key={subject.id}
              role="button"
              tabIndex={0}
              aria-label={`Open study session for ${subject.name}, active topic ${subject.topic}`}
              onClick={() => handleLaunchQuickSession(subject.topic)}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleLaunchQuickSession(subject.topic)}
              className="glass-card p-6 rounded-2xl border border-[#232D3F] hover:border-[#6366F1]/50 cursor-pointer transition-all duration-300 group hover:-translate-y-1 focus:outline-none focus:ring-2 focus:ring-[#6366F1]"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-xl bg-[#6366F1]/10 border border-[#6366F1]/20 flex items-center justify-center text-[#6366F1] group-hover:scale-110 transition-transform">
                  <BookOpen className="w-5 h-5" aria-hidden="true" />
                </div>
                <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/20">
                  {subject.mastery} Mastery
                </span>
              </div>

              <h4 className="font-bold text-base text-white group-hover:text-[#6366F1] transition-colors">{subject.name}</h4>
              <p className="text-xs text-[#9CA3AF] mt-1">{subject.files} Study Files Ingested</p>

              <div className="mt-6 pt-4 border-t border-[#232D3F] flex items-center justify-between text-xs text-[#9CA3AF]">
                <span>Active: <strong className="text-white">{subject.topic}</strong></span>
                <ArrowRight className="w-4 h-4 text-[#6366F1] group-hover:translate-x-1 transition-transform" aria-hidden="true" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
