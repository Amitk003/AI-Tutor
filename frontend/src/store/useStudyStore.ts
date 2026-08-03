import { create } from 'zustand';

export interface MiniQuizItem {
  question_id: string;
  question_type: string;
  question_text: string;
  code_snippet?: string;
  correct_answer: string;
  distractors: Array<{
    option_text: string;
    misconception_represented: string;
    explanation: string;
  }>;
  calibrated_difficulty: number;
  explanation: string;
}

export interface StudyTurnMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  pedagogy?: {
    strategy: string;
    rationale: string;
    difficulty_level: string;
    selected_modalities: string[];
  };
  miniQuiz?: MiniQuizItem;
  citations?: Array<{
    document_id: string;
    page_number: number;
    section_title: string;
    snippet: string;
  }>;
}

interface StudyState {
  activeSessionId: string | null;
  activeConcept: string;
  messages: StudyTurnMessage[];
  currentMiniQuiz: MiniQuizItem | null;
  isSessionActive: boolean;
  startSession: (sessionId: string, concept: string) => void;
  addMessage: (message: StudyTurnMessage) => void;
  setCurrentMiniQuiz: (quiz: MiniQuizItem | null) => void;
  clearSession: () => void;
}

export const useStudyStore = create<StudyState>((set) => ({
  activeSessionId: null,
  activeConcept: 'Binary Search Tree',
  messages: [],
  currentMiniQuiz: null,
  isSessionActive: false,

  startSession: (sessionId: string, concept: string) => {
    set({
      activeSessionId: sessionId,
      activeConcept: concept,
      messages: [],
      currentMiniQuiz: null,
      isSessionActive: true,
    });
  },

  addMessage: (message: StudyTurnMessage) => {
    set((state) => ({
      messages: [...state.messages, message],
      currentMiniQuiz: message.miniQuiz || state.currentMiniQuiz,
    }));
  },

  setCurrentMiniQuiz: (quiz: MiniQuizItem | null) => {
    set({ currentMiniQuiz: quiz });
  },

  clearSession: () => {
    set({
      activeSessionId: null,
      messages: [],
      currentMiniQuiz: null,
      isSessionActive: false,
    });
  },
}));
