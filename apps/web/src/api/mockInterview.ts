import type { InterviewNextResponse, InterviewQuestion } from '../contracts';

export type QuestionHint = {
  label: string;
  unit?: string;
  min?: number;
  max?: number;
  step?: number;
};

// FRONTEND-ONLY PLACEHOLDER until Person A ships interview mocks.
// Question wording is from the project spec (Offer X-ray). Variable names come
// from the spec's example and may not match the real Decision Spec. Slider
// bounds are provisional UI limits, not business rules.
export const MOCK_QUESTIONS: InterviewQuestion[] = [
  { id: 'q_tenure', text: 'How long do you expect to stay in the job?', answer_type: 'range', variable: 'tenure_months', required: true },
  { id: 'q_rent', text: 'What monthly rent will you pay?', answer_type: 'value', variable: 'monthly_rent', required: true },
  { id: 'q_tax', text: 'Which tax regime will you use?', answer_type: 'choice', variable: 'tax_regime', required: true, choices: ['new', 'old'] },
  { id: 'q_payout', text: 'What share of the target variable pay do you expect to actually receive?', answer_type: 'range', variable: 'A.variable_payout', required: false },
];

export const QUESTION_HINTS: Record<string, QuestionHint> = {
  q_tenure: { label: 'Time in the job', unit: 'months', min: 6, max: 48, step: 1 },
  q_rent: { label: 'Monthly rent', unit: '₹/month' },
  q_tax: { label: 'Tax regime' },
  q_payout: { label: 'Variable pay received', unit: 'of target', min: 0, max: 1, step: 0.05 },
};

// Mimics GET /sessions/{id}/interview/next
export function mockNextQuestion(answeredIds: string[]): InterviewNextResponse {
  const question = MOCK_QUESTIONS.find((q) => !answeredIds.includes(q.id)) ?? null;
  return { done: question === null, question };
}