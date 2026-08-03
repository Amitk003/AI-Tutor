import React, { useState } from 'react';
import { Brain, CheckCircle, AlertTriangle, Sparkles, RefreshCw, ArrowRight } from 'lucide-react';
import { apiClient } from '../api/client';

export const AssessmentPage: React.FC = () => {
  const [conceptName, setConceptName] = useState('Binary Search Tree');
  const [questionCount, setQuestionCount] = useState(3);
  const [quizData, setQuizData] = useState<any | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [evaluationResults, setEvaluationResults] = useState<Record<string, any>>({});

  const handleGenerateQuiz = async () => {
    setIsGenerating(true);
    setQuizData(null);
    setSelectedAnswers({});
    setEvaluationResults({});
    setErrorMessage('');

    try {
      const res = await apiClient.post('/quiz/generate', {
        concept_name: conceptName,
        question_count: questionCount,
        question_type: 'MCQ',
      });
      setQuizData(res.data);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.error?.message || 'Quiz generation failed. Check that the configured LLM service is available.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectOption = (qId: string, option: string) => {
    setSelectedAnswers({ ...selectedAnswers, [qId]: option });
  };

  const handleSubmitAnswer = async (q: any) => {
    const studentAnswer = selectedAnswers[q.question_id];
    if (!studentAnswer) return;

    try {
      const res = await apiClient.post('/quiz/evaluate', {
        quiz_id: quizData.quiz_id,
        question_id: q.question_id,
        concept_name: conceptName,
        student_answer: studentAnswer,
        correct_answer: q.correct_answer,
        distractors: q.distractors,
        calibrated_difficulty: q.calibrated_difficulty,
      });

      setEvaluationResults({ ...evaluationResults, [q.question_id]: res.data });
    } catch (err: any) {
      setErrorMessage(err.response?.data?.error?.message || 'Answer evaluation failed. Please try again.');
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Adaptive Assessment Center</h2>
        <p className="text-xs text-[#9CA3AF] mt-1">
          Generate IRT-calibrated questions tailored to your ability parameter ($\theta$). Every distractor option identifies specific misconceptions.
        </p>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400">
          {errorMessage}
        </div>
      )}

      {/* Quiz Configurator */}
      <div className="glass-card p-6 rounded-2xl border border-[#232D3F] flex flex-col md:flex-row items-end justify-between gap-4">
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
          <div>
            <label className="block text-xs font-medium text-[#9CA3AF] mb-1">Target Subject / Concept</label>
            <input
              type="text"
              value={conceptName}
              onChange={(e) => setConceptName(e.target.value)}
              className="w-full px-4 py-2.5 bg-[#0B0F17] border border-[#232D3F] rounded-xl text-xs text-white focus:border-[#6366F1] focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#9CA3AF] mb-1">Number of Items</label>
            <select
              value={questionCount}
              onChange={(e) => setQuestionCount(Number(e.target.value))}
              className="w-full px-4 py-2.5 bg-[#0B0F17] border border-[#232D3F] rounded-xl text-xs text-white focus:border-[#6366F1] focus:outline-none"
            >
              <option value={3}>3 Questions (Quick Check)</option>
              <option value={5}>5 Questions (Standard)</option>
              <option value={10}>10 Questions (Comprehensive)</option>
            </select>
          </div>
        </div>

        <button
          onClick={handleGenerateQuiz}
          disabled={isGenerating}
          className="w-full md:w-auto px-6 py-2.5 bg-[#6366F1] hover:bg-[#6366F1]/90 text-white rounded-xl font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-[#6366F1]/25 transition-all disabled:opacity-50"
        >
          {isGenerating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
          <span>{isGenerating ? 'Calibrating Questions...' : 'Generate Adaptive Quiz'}</span>
        </button>
      </div>

      {/* Render Quiz Items */}
      {quizData && (
        <div className="space-y-6">
          <div className="p-4 rounded-xl bg-[#6366F1]/10 border border-[#6366F1]/20 flex items-center justify-between text-xs text-[#6366F1]">
            <span className="font-semibold">Target IRT Ability: θ = {quizData.plan.target_difficulty.toFixed(2)}</span>
            <span>Objective: {quizData.plan.assessment_objective}</span>
          </div>

          {quizData.questions.map((q: any, idx: number) => {
            const selected = selectedAnswers[q.question_id];
            const evalRes = evaluationResults[q.question_id];
            const allOptions = [q.correct_answer, ...q.distractors.map((d: any) => d.option_text)];

            return (
              <div key={q.question_id} className="glass-card p-6 rounded-2xl border border-[#232D3F] space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#6366F1]">Question {idx + 1} of {quizData.questions.length}</span>
                  <span className="text-[10px] text-[#9CA3AF]">Calibrated Difficulty b = {q.calibrated_difficulty.toFixed(2)}</span>
                </div>

                <h3 className="text-sm font-bold text-white">{q.question_text}</h3>

                <div className="space-y-2">
                  {allOptions.map((opt, i) => (
                    <button
                      key={i}
                      onClick={() => handleSelectOption(q.question_id, opt)}
                      className={`w-full text-left p-3.5 rounded-xl border text-xs transition-all ${
                        selected === opt
                          ? 'bg-[#6366F1]/20 border-[#6366F1] text-white font-bold'
                          : 'bg-[#0B0F17] border-[#232D3F] text-[#9CA3AF] hover:text-white hover:border-[#6366F1]/40'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>

                {!evalRes ? (
                  <button
                    onClick={() => handleSubmitAnswer(q)}
                    disabled={!selected}
                    className="px-4 py-2 bg-[#6366F1] hover:bg-[#6366F1]/90 text-white text-xs font-semibold rounded-lg shadow-md transition-all disabled:opacity-50"
                  >
                    Submit Answer
                  </button>
                ) : (
                  <div className={`p-4 rounded-xl border text-xs ${
                    evalRes.is_correct ? 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]' : 'bg-red-500/10 border-red-500/30 text-red-400'
                  }`}>
                    <div className="flex items-center gap-2 font-bold mb-1">
                      {evalRes.is_correct ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                      <span>{evalRes.is_correct ? 'Correct! IRT Ability θ updated.' : 'Incorrect answer.'}</span>
                    </div>
                    <p className="mt-1 text-white">{q.explanation}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
