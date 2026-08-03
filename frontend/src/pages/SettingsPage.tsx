import React, { useEffect, useState } from 'react';
import { Settings, Sparkles, CheckCircle, Save } from 'lucide-react';
import { apiClient } from '../api/client';

export const SettingsPage: React.FC = () => {
  const [explanationStyle, setExplanationStyle] = useState('Socratic');
  const [language, setLanguage] = useState('en');
  const [theme, setTheme] = useState('dark');
  const [gradeLevel, setGradeLevel] = useState('Undergraduate');
  const [saveSuccess, setSaveSuccess] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await apiClient.get('/student/profile');
        if (res.data) {
          setExplanationStyle(res.data.preferred_explanation_style || 'Socratic');
          setLanguage(res.data.preferred_language || 'en');
          setTheme(res.data.theme || 'dark');
          setGradeLevel(res.data.grade_level || 'Undergraduate');
        }
      } catch (err) {
        console.warn('Profile fetch fallback');
      }
    };
    fetchProfile();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSaveSuccess('');

    try {
      await apiClient.patch('/student/preferences', {
        preferred_explanation_style: explanationStyle,
        preferred_language: language,
        theme,
      });
      setSaveSuccess('Pedagogical preferences saved successfully!');
    } catch (err) {
      alert('Failed to save preferences.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Student Settings & Preferences</h2>
        <p className="text-xs text-[#9CA3AF] mt-1">
          Customize your AI Companion's teaching strategy, academic level, and interface options.
        </p>
      </div>

      <form onSubmit={handleSave} className="glass-card p-8 rounded-2xl border border-[#232D3F] space-y-6">
        {saveSuccess && (
          <div className="p-3.5 rounded-xl bg-[#10B981]/10 border border-[#10B981]/20 text-xs text-[#10B981] flex items-center gap-2">
            <CheckCircle className="w-4 h-4" /> {saveSuccess}
          </div>
        )}

        <div>
          <label className="block text-xs font-bold text-white mb-2">Preferred Teaching Strategy</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { id: 'Socratic', title: 'Socratic Guided Questioning', desc: 'Asks reflective questions leading you to self-discovery.' },
              { id: 'Feynman', title: 'Feynman / ELI5 Method', desc: 'Uses simplified terminology and fundamental breakdowns.' },
              { id: 'Analogy', title: 'Real-World Analogies', desc: 'Relates abstract topics to physical metaphors.' },
              { id: 'Academic', title: 'Direct Academic Instruction', desc: 'Clear, structured, authoritative explanations.' },
            ].map((style) => (
              <div
                key={style.id}
                onClick={() => setExplanationStyle(style.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${
                  explanationStyle === style.id
                    ? 'bg-[#6366F1]/10 border-[#6366F1] text-white shadow-md'
                    : 'bg-[#0B0F17] border-[#232D3F] text-[#9CA3AF] hover:border-[#6366F1]/40'
                }`}
              >
                <h4 className="text-xs font-bold text-white">{style.title}</h4>
                <p className="text-[11px] text-[#9CA3AF] mt-1">{style.desc}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-white mb-1">Academic Grade Level</label>
            <select
              value={gradeLevel}
              onChange={(e) => setGradeLevel(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0B0F17] border border-[#232D3F] rounded-xl text-xs text-white focus:border-[#6366F1] focus:outline-none"
            >
              <option value="High School">High School</option>
              <option value="Undergraduate">Undergraduate Student</option>
              <option value="Graduate">Graduate / Postgraduate</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-white mb-1">Preferred Language</label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0B0F17] border border-[#232D3F] rounded-xl text-xs text-white focus:border-[#6366F1] focus:outline-none"
            >
              <option value="en">English (EN)</option>
              <option value="es">Spanish (ES)</option>
              <option value="fr">French (FR)</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSaving}
          className="px-6 py-2.5 bg-[#6366F1] hover:bg-[#6366F1]/90 text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-lg shadow-[#6366F1]/25 transition-all disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          <span>{isSaving ? 'Saving...' : 'Save Settings'}</span>
        </button>
      </form>
    </div>
  );
};
