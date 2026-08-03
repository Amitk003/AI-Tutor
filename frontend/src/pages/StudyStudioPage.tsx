import React, { useState } from 'react';
import { Sparkles, Send, BookOpen, Brain, CheckCircle, AlertTriangle, ArrowRight, RefreshCw, PanelRightClose, PanelRightOpen } from 'lucide-react';
import { apiClient } from '../api/client';
import { MarkdownRenderer } from '../components/common/MarkdownRenderer';
import { useStudyStore, MiniQuizItem } from '../store/useStudyStore';

export const StudyStudioPage: React.FC = () => {
  const { activeSessionId, activeConcept, messages, currentMiniQuiz, addMessage, setCurrentMiniQuiz } = useStudyStore();

  const [inputQuery, setInputQuery] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [quizEvaluated, setQuizEvaluated] = useState<any | null>(null);
  const [showSourceViewer, setShowSourceViewer] = useState(false);
  const [sessionCompleted, setSessionCompleted] = useState(false);

  const [sessionId] = useState(() => activeSessionId || crypto.randomUUID());
  const [errorMessage, setErrorMessage] = useState('');

  const handleSendQuery = async (overrideQuery?: string, answerToSubmit?: string) => {
    const qText = overrideQuery || inputQuery;
    if (!qText.trim() || isGenerating) return;

    setInputQuery('');
    setIsGenerating(true);
    setErrorMessage('');

    // Add User Message
    addMessage({
      id: `user-${Date.now()}`,
      role: 'user',
      content: qText,
    });

    try {
      const res = await apiClient.post('/study/session', {
        session_id: sessionId,
        concept_name: activeConcept,
        question: qText,
        student_answer: answerToSubmit || null,
        quiz_item: currentMiniQuiz || null,
      });

      const data = res.data;
      const teaching = data.teaching_explanation || {};
      const miniQuiz: MiniQuizItem | undefined = data.check_understanding_mini_quiz;

      // Add Assistant Teaching Response Message
      addMessage({
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: teaching.answer || 'Grounded explanation generated based on study materials.',
        pedagogy: teaching.pedagogy,
        miniQuiz: miniQuiz,
        citations: teaching.citations,
      });

      if (miniQuiz) {
        setCurrentMiniQuiz(miniQuiz);
        setSelectedOption(null);
        setQuizEvaluated(null);
      }
    } catch (err: any) {
      setErrorMessage(err.response?.data?.error?.message || 'Study response failed. Check that your documents are indexed and the LLM service is available.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleQuizSubmit = async (optionText: string) => {
    setSelectedOption(optionText);
    if (!currentMiniQuiz) return;

    const isCorrect = optionText.trim().lowerCase === currentMiniQuiz.correct_answer.trim().lowerCase;
    const matchedDistractor = currentMiniQuiz.distractors.find(
      (d) => d.option_text.trim().lowerCase === optionText.trim().lowerCase
    );

    try {
      const res = await apiClient.post('/quiz/evaluate', {
        quiz_id: sessionId,
        question_id: currentMiniQuiz.question_id,
        concept_name: activeConcept,
        student_answer: optionText,
        correct_answer: currentMiniQuiz.correct_answer,
        distractors: currentMiniQuiz.distractors,
        calibrated_difficulty: currentMiniQuiz.calibrated_difficulty,
      });
      setQuizEvaluated({
        ...res.data,
        correct_answer: currentMiniQuiz.correct_answer,
        explanation: currentMiniQuiz.explanation,
        misconception: matchedDistractor?.misconception_represented,
        distractor_explanation: matchedDistractor?.explanation,
      });
    } catch (err: any) {
      setErrorMessage(err.response?.data?.error?.message || 'Mini-quiz evaluation failed.');
      setQuizEvaluated(null);
    }
  };

  const handleCompleteSession = async () => {
    try {
      await apiClient.post('/study/complete', {
        session_id: sessionId,
        concepts_studied: [activeConcept],
        duration_seconds: 420,
      });
      setSessionCompleted(true);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.error?.message || 'Could not complete this study session.');
    }
  };

  return (
    <div className="flex gap-6 h-[calc(100vh-7rem)]">
      {/* Primary Study Companion Studio Feed */}
      <div className="flex-1 flex flex-col min-w-0 glass-panel rounded-2xl border border-[#232D3F] overflow-hidden">
        {/* Studio Session Header */}
        <div className="px-6 py-4 border-b border-[#232D3F] bg-[#161B26]/80 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#6366F1]/10 border border-[#6366F1]/20 flex items-center justify-center text-[#6366F1]">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Studying: {activeConcept}</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20 font-semibold">
                  Grounded RAG
                </span>
              </h2>
              <p className="text-[10px] text-[#9CA3AF]">Adaptive Socratic Tutoring Session</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSourceViewer(!showSourceViewer)}
              className="px-3 py-1.5 rounded-lg bg-[#0B0F17] border border-[#232D3F] text-xs font-medium text-[#9CA3AF] hover:text-white flex items-center gap-1.5 transition-colors"
            >
              {showSourceViewer ? <PanelRightClose className="w-3.5 h-3.5" /> : <PanelRightOpen className="w-3.5 h-3.5" />}
              <span>{showSourceViewer ? 'Hide Source PDF' : 'View Source PDF'}</span>
            </button>

            <button
              onClick={handleCompleteSession}
              className="px-3.5 py-1.5 rounded-lg bg-[#10B981]/10 border border-[#10B981]/20 text-[#10B981] hover:bg-[#10B981] hover:text-black text-xs font-bold transition-all"
            >
              Finish Session
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400">
            {errorMessage}
          </div>
        )}

        {/* Streaming Messages Feed */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-[#6366F1]/10 border border-[#6366F1]/20 flex items-center justify-center text-[#6366F1] mb-4">
                <Sparkles className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Start your 1-on-1 Study Turn</h3>
              <p className="text-xs text-[#9CA3AF] mt-1">
                Ask a question about <strong className="text-white">{activeConcept}</strong>. Your AI Companion will teach you directly from your uploaded slides with diagrams and mini-quizzes.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {['Explain search time complexity', 'Draw process flowchart', 'Compare BST vs AVL Tree'].map((chip) => (
                  <button
                    key={chip}
                    onClick={() => handleSendQuery(chip)}
                    className="px-3 py-1.5 rounded-full bg-[#161B26] border border-[#232D3F] text-xs text-[#9CA3AF] hover:text-white hover:border-[#6366F1] transition-all"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#6366F1] to-[#8B5CF6] flex items-center justify-center text-white shrink-0 mt-1 shadow-md">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-2xl rounded-2xl p-5 border ${
                  msg.role === 'user'
                    ? 'bg-[#6366F1] text-white border-[#6366F1]'
                    : 'bg-[#161B26] border-[#232D3F] shadow-xl'
                }`}>
                  {msg.role === 'assistant' && msg.pedagogy && (
                    <div className="mb-3 inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#0B0F17] border border-[#232D3F] text-[10px] font-semibold text-[#8B5CF6]">
                      <span>Strategy: {msg.pedagogy.strategy}</span>
                      <span>•</span>
                      <span>Level: {msg.pedagogy.difficulty_level}</span>
                    </div>
                  )}

                  <MarkdownRenderer content={msg.content} />

                  {/* Inline Grounded Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-[#232D3F] flex flex-wrap gap-2 text-[10px] text-[#9CA3AF]">
                      <span className="font-semibold text-white">Sources:</span>
                      {msg.citations.map((c, i) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-[#0B0F17] border border-[#232D3F] text-[#6366F1]">
                          Page {c.page_number}, {c.section_title}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}

          {/* Embedded Check-Understanding Mini-Quiz Component */}
          {currentMiniQuiz && (
            <div className="p-6 rounded-2xl bg-[#161B26] border-2 border-[#6366F1]/40 shadow-2xl space-y-4 my-6">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-full bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20 text-xs font-bold flex items-center gap-1.5">
                  <Brain className="w-3.5 h-3.5" /> Check Understanding Mini-Quiz
                </span>
                <span className="text-[10px] text-[#9CA3AF]">Calibrated Difficulty (b = {currentMiniQuiz.calibrated_difficulty.toFixed(2)})</span>
              </div>

              <h3 className="text-sm font-bold text-white">{currentMiniQuiz.question_text}</h3>

              <div className="space-y-2">
                {[currentMiniQuiz.correct_answer, ...currentMiniQuiz.distractors.map((d) => d.option_text)].map((opt, i) => {
                  const isSelected = selectedOption === opt;
                  return (
                    <button
                      key={i}
                      onClick={() => handleQuizSubmit(opt)}
                      className={`w-full text-left p-3.5 rounded-xl border text-xs font-medium transition-all ${
                        isSelected
                          ? 'bg-[#6366F1]/20 border-[#6366F1] text-white font-bold'
                          : 'bg-[#0B0F17] border-[#232D3F] text-[#9CA3AF] hover:text-white hover:border-[#6366F1]/40'
                      }`}
                    >
                      {opt}
                    </button>
                  );
                })}
              </div>

              {quizEvaluated && (
                <div className={`p-4 rounded-xl border text-xs ${
                  quizEvaluated.is_correct
                    ? 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]'
                    : 'bg-red-500/10 border-red-500/30 text-red-400'
                }`}>
                  <div className="flex items-center gap-2 font-bold mb-1">
                    {quizEvaluated.is_correct ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                    <span>{quizEvaluated.is_correct ? 'Correct! Your learning model has been updated.' : 'Incorrect choice.'}</span>
                  </div>
                  <p className="mt-1 text-white">{quizEvaluated.explanation}</p>
                  {quizEvaluated.misconception && (
                    <p className="mt-2 text-amber-400 text-[11px]">
                      <strong>Misconception Detected:</strong> {quizEvaluated.misconception} ({quizEvaluated.distractor_explanation})
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {sessionCompleted && (
            <div className="p-6 rounded-2xl bg-gradient-to-tr from-[#161B26] to-[#1E2536] border border-[#10B981]/40 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 flex items-center justify-center text-[#10B981] mx-auto">
                <CheckCircle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Study Session Complete!</h3>
              <p className="text-xs text-[#9CA3AF]">Your study session has been recorded and the revision schedule was updated.</p>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-[#232D3F] bg-[#161B26]/90 flex items-center gap-3">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendQuery()}
            placeholder={`Ask your AI Companion a question about ${activeConcept}...`}
            disabled={isGenerating}
            className="flex-1 px-4 py-3 bg-[#0B0F17] border border-[#232D3F] rounded-xl text-xs text-white placeholder-[#9CA3AF]/50 focus:outline-none focus:border-[#6366F1]"
          />

          <button
            onClick={() => handleSendQuery()}
            disabled={isGenerating || !inputQuery.trim()}
            className="p-3 bg-[#6366F1] hover:bg-[#6366F1]/90 text-white rounded-xl shadow-lg shadow-[#6366F1]/25 transition-all disabled:opacity-50"
          >
            {isGenerating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Optional Grounded Source PDF Viewer Pane */}
      {showSourceViewer && (
        <div className="w-96 glass-panel rounded-2xl border border-[#232D3F] p-4 flex flex-col hidden lg:flex">
          <div className="flex items-center justify-between pb-3 border-b border-[#232D3F]">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-[#6366F1]" />
              <h3 className="text-xs font-bold text-white">Course Source Material</h3>
            </div>
            <span className="text-[10px] text-[#9CA3AF]">Page 14 of 42</span>
          </div>

          <div className="flex-1 mt-4 p-4 rounded-xl bg-[#0B0F17] border border-[#232D3F] text-xs text-[#9CA3AF] overflow-y-auto space-y-3">
            <div className="p-2 rounded bg-[#6366F1]/10 border border-[#6366F1]/20 text-white font-medium">
              [Page 14, Section 3.2] Binary Search Tree Properties
            </div>
            <p>
              A Binary Search Tree is a node-based binary tree data structure with the property that the left subtree contains nodes with keys less than the parent.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
