import { useState } from 'react';
import type { InterviewAnswerRequest, InterviewQuestion } from '../contracts';
import type { QuestionHint } from '../api/mockInterview';

export type AnswerValue = InterviewAnswerRequest['value'];

type Props = {
  question: InterviewQuestion;
  hint: QuestionHint;
  initial?: AnswerValue;
  onSubmit: (value: AnswerValue) => void;
};

export function QuestionForm({ question, hint, initial, onSubmit }: Props) {
  const min = hint.min ?? 0;
  const max = hint.max ?? 100;
  const step = hint.step ?? 1;

  const [num, setNum] = useState(typeof initial === 'number' ? String(initial) : '');
  const [range, setRange] = useState<{ low: number; high: number }>(
    typeof initial === 'object' ? { low: initial.low, high: initial.high } : { low: min, high: max },
  );
  const [choice, setChoice] = useState<string | number | boolean | null>(
    initial === undefined || typeof initial === 'object' ? null : initial,
  );

  const canSubmit =
    question.answer_type === 'value'
      ? num.trim() !== '' && Number.isFinite(Number(num))
      : question.answer_type === 'choice'
        ? choice !== null
        : true;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    if (question.answer_type === 'range') onSubmit({ low: range.low, high: range.high });
    else if (question.answer_type === 'choice' && choice !== null) onSubmit(choice);
    else onSubmit(Number(num));
  }

  return (
    <form onSubmit={submit} className="glass p-6">
      <p className="font-display text-2xl font-semibold">{question.text}</p>
      {!question.required && <p className="mt-1 text-xs text-muted">Optional</p>}

      {question.answer_type === 'value' && (
        <div className="mt-4">
          <label htmlFor="answer" className="text-sm text-muted">
            Your answer{hint.unit ? ` (${hint.unit})` : ''}
          </label>
          <input
            id="answer"
            inputMode="decimal"
            value={num}
            onChange={(e) => setNum(e.target.value)}
            className="mt-1 w-full rounded-control bg-white/5 px-3 py-2 font-mono"
          />
        </div>
      )}

      {question.answer_type === 'choice' && (
        <fieldset className="mt-4 space-y-2">
          <legend className="text-sm text-muted">Choose one</legend>
          {(question.choices ?? []).map((c) => (
            <label key={String(c)} className="flex items-center gap-2">
              <input type="radio" name={question.id} checked={choice === c} onChange={() => setChoice(c)} />
              {String(c)}
            </label>
          ))}
        </fieldset>
      )}

      {question.answer_type === 'range' && (
        <div className="mt-4">
          <p className="font-mono text-lg" aria-live="polite">
            {range.low} to {range.high} {hint.unit ?? ''}
          </p>
          <label htmlFor="low" className="mt-3 block text-sm text-muted">Lowest you expect</label>
          <input
            id="low"
            type="range"
            min={min}
            max={max}
            step={step}
            value={range.low}
            onChange={(e) => setRange((r) => ({ ...r, low: Math.min(Number(e.target.value), r.high) }))}
            className="w-full"
          />
          <label htmlFor="high" className="mt-3 block text-sm text-muted">Highest you expect</label>
          <input
            id="high"
            type="range"
            min={min}
            max={max}
            step={step}
            value={range.high}
            onChange={(e) => setRange((r) => ({ ...r, high: Math.max(Number(e.target.value), r.low) }))}
            className="w-full"
          />
        </div>
      )}

      <button type="submit" disabled={!canSubmit} className="glass mt-6 px-5 py-2 disabled:opacity-50">
        Save answer
      </button>
    </form>
  );
}