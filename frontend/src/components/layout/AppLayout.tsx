import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Sparkles,
  Brain,
  CheckCircle2,
  Settings,
  LayoutDashboard,
  LogOut,
  User,
  Zap,
} from 'lucide-react';
import { useAuthStore } from '../../store/useAuthStore';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Subjects', path: '/subjects', icon: BookOpen },
    { label: 'Study Studio', path: '/study', icon: Sparkles, badge: 'AI' },
    { label: 'Quizzes', path: '/quizzes', icon: Brain },
    { label: 'Revision', path: '/revision', icon: CheckCircle2 },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  const handleLogout = () => {
    logout();
    navigate('/auth');
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] flex flex-col md:flex-row text-[#F9FAFB]">
      {/* Desktop Sidebar Navigation */}
      <aside
        aria-label="Main Navigation"
        className="hidden md:flex flex-col w-64 border-r border-[#232D3F] bg-[#161B26]/80 backdrop-blur-xl p-5 justify-between sticky top-0 h-screen z-30"
      >
        <div>
          {/* Logo & Brand Header */}
          <div className="flex items-center gap-3 px-2 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#6366F1] to-[#8B5CF6] flex items-center justify-center shadow-lg shadow-[#6366F1]/20">
              <Sparkles className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-tight text-white leading-none">Study Companion</h1>
              <span className="text-[10px] font-semibold tracking-wider text-[#6366F1] uppercase">AI Tutoring</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5" aria-label="Primary Desktop Menu">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  aria-current={isActive ? 'page' : undefined}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#6366F1] ${
                    isActive
                      ? 'bg-[#6366F1] text-white shadow-lg shadow-[#6366F1]/25 font-semibold'
                      : 'text-[#9CA3AF] hover:text-white hover:bg-[#232D3F]/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-[#9CA3AF]'}`} aria-hidden="true" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-[#8B5CF6] text-white">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Card & Logout Button */}
        <div className="border-t border-[#232D3F] pt-4 space-y-3">
          <div className="flex items-center gap-3 px-2 py-1.5 rounded-xl bg-[#0B0F17]/50 border border-[#232D3F]">
            <div className="w-8 h-8 rounded-lg bg-[#232D3F] flex items-center justify-center text-[#9CA3AF]">
              <User className="w-4 h-4 text-[#6366F1]" aria-hidden="true" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user?.full_name || 'Student Workspace'}</p>
              <p className="text-[10px] text-[#9CA3AF] truncate">{user?.email || 'student@platform.ai'}</p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            aria-label="Sign out of student account"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-[#9CA3AF] hover:text-red-400 hover:bg-red-500/10 focus:outline-none focus:ring-2 focus:ring-red-500/50 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Navigation */}
        <header className="h-16 border-b border-[#232D3F] bg-[#161B26]/60 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20 flex items-center gap-1.5">
              <Zap className="w-3 h-3 text-[#6366F1]" aria-hidden="true" /> Grounded RAG Engine Active
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <span className="text-xs text-[#9CA3AF] block">Current Session</span>
              <span className="text-xs font-semibold text-white">Undergraduate Mode</span>
            </div>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main id="main-content" className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto pb-24 md:pb-8">
          {children}
        </main>

        {/* Mobile Bottom Navigation Bar */}
        <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-[#161B26] border-t border-[#232D3F] flex items-center justify-around z-40 px-2" aria-label="Mobile Bottom Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                aria-current={isActive ? 'page' : undefined}
                className={`flex flex-col items-center gap-1 px-3 py-1 rounded-lg text-[10px] font-medium transition-colors focus:outline-none ${
                  isActive ? 'text-[#6366F1] font-bold' : 'text-[#9CA3AF]'
                }`}
              >
                <Icon className="w-5 h-5" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
};
