import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Lock, Mail, User, ArrowRight, ShieldCheck } from 'lucide-react';
import { apiClient } from '../api/client';
import { useAuthStore } from '../store/useAuthStore';

export const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);

    try {
      if (isLogin) {
        const res = await apiClient.post('/auth/login', { email, password });

        const token = res.data.access_token;
        const userRes = await apiClient.get('/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        });

        login(token, userRes.data);
        navigate('/dashboard');
      } else {
        await apiClient.post('/auth/signup', {
          email,
          password,
          full_name: fullName,
        });

        // Auto login after signup
        const res = await apiClient.post('/auth/login', { email, password });

        const token = res.data.access_token;
        const userRes = await apiClient.get('/auth/me', {
          headers: { Authorization: `Bearer ${token}` },
        });

        login(token, userRes.data);
        navigate('/dashboard');
      }
    } catch (err: any) {
      const detail = err.response?.data?.error?.message || err.response?.data?.detail || 'Authentication failed. Please check your inputs.';
      setErrorMsg(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Brand Logo & Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-[#6366F1] to-[#8B5CF6] flex items-center justify-center mx-auto mb-4 shadow-xl shadow-[#6366F1]/25">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">AI Study Companion</h1>
          <p className="text-xs text-[#9CA3AF] mt-1">Personalized closed-domain 1-on-1 tutoring engine</p>
        </div>

        {/* Auth Card */}
        <div className="glass-card p-6 rounded-2xl border border-[#232D3F] shadow-2xl">
          {/* Tab Selection */}
          <div className="grid grid-cols-2 p-1 bg-[#0B0F17] rounded-xl mb-6 border border-[#232D3F]">
            <button
              onClick={() => { setIsLogin(true); setErrorMsg(''); }}
              className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                isLogin ? 'bg-[#6366F1] text-white shadow-md' : 'text-[#9CA3AF] hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setIsLogin(false); setErrorMsg(''); }}
              className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                !isLogin ? 'bg-[#6366F1] text-white shadow-md' : 'text-[#9CA3AF] hover:text-white'
              }`}
            >
              Register
            </button>
          </div>

          {errorMsg && (
            <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-xs text-red-400">
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-xs font-medium text-[#9CA3AF] mb-1">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-[#9CA3AF] absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Alex Student"
                    className="w-full pl-9 pr-4 py-2.5 bg-[#0B0F17] border border-[#232D3F] rounded-xl text-xs text-white placeholder-[#9CA3AF]/50 focus:outline-none focus:border-[#6366F1]"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-[#9CA3AF] mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-[#9CA3AF] absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@university.edu"
                  className="w-full pl-9 pr-4 py-2.5 bg-[#0B0F17] border border-[#232D3F] rounded-xl text-xs text-white placeholder-[#9CA3AF]/50 focus:outline-none focus:border-[#6366F1]"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[#9CA3AF] mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#9CA3AF] absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-9 pr-4 py-2.5 bg-[#0B0F17] border border-[#232D3F] rounded-xl text-xs text-white placeholder-[#9CA3AF]/50 focus:outline-none focus:border-[#6366F1]"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-3 px-4 bg-[#6366F1] hover:bg-[#6366F1]/90 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 shadow-lg shadow-[#6366F1]/25 transition-all disabled:opacity-50"
            >
              {isLoading ? (
                <span>Authenticating...</span>
              ) : (
                <>
                  <span>{isLogin ? 'Sign In to Workspace' : 'Create Student Account'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-[#232D3F] flex items-center justify-center gap-2 text-[10px] text-[#9CA3AF]">
            <ShieldCheck className="w-3.5 h-3.5 text-[#10B981]" />
            <span>Zero-Retraining Privacy & Isolated Student Model</span>
          </div>
        </div>
      </div>
    </div>
  );
};
