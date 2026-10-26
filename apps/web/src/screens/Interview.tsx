import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ScreenStub } from '../components/ScreenStub';
import { QuestionForm, type AnswerValue } from '../components/QuestionForm';
import { MOCK_QUESTIONS, QUESTION_HINTS, mockNextQuestion } from '../api/mockInterview';

function valueText(v: AnswerValue, unit?: string) {
  const base = typeof v === 'object' ? `${v.low} to ${v.high}` : String(v);
  return unit ? `${base} ${unit}` : base;
}

export default function Interview() {
  const { id = 'demo_offer_xray' } = useParams();
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>({});
  const [editingId, setEditingId] = useState<string | null>(null);

  const next = mockNextQuestion(Object.keys(answers));
  const question = editingId ? (MOCK_QUESTIONS.find((q) => q.id === editingId) ?? null) : next.question;
  const answered = MOCK_QUESTIONS.filter((q) => q.id in answers);

  function save(questionId: string, value: AnswerValue) {
    setAnswers((prev) => ({ ...prev, [questionId]: value }));
    setEditingId(null);
  }

  return (
    <>
      <ScreenStub title="Interview" />
      <section className="mx-auto max-w-5xl px-8 pb-16">
        <p className="font-mono text-sm text-flip">
          PLACEHOLDER QUESTIONS · frontend-only until the backend provides them · answers are not sent anywhere
        </p>

        <div className="mt-6 grid gap-6 md:grid-cols-[minmax(0,260px)_1fr]">
          <aside aria-label="Your assumptions">
            <h2 className="font-display text-lg font-semibold">Your assumptions</h2>
            {answered.length === 0 ? (
              <p className="mt-2 text-sm text-muted">None yet.</p>
            ) : (
              <ul className="mt-2 space-y-2">
                {answered.map((q) => {
                  const hint = QUESTION_HINTS[q.id] ?? { label: q.variable };
                  const value = answers[q.id];
                  return (
                    <li key={q.id}>
                      <button
                        type="button"
                        onClick={() => setEditingId(q.id)}
                        className="glass w-full px-3 py-2 text-left"
                      >
                        <span className="block text-xs text-muted">{hint.label} · You</span>
                        <span className="block font-mono text-sm">
                          {value === undefined ? '' : valueText(value, hint.unit)}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </aside>

          <div>
            {question ? (
              <QuestionForm
                key={question.id}
                question={question}
                hint={QUESTION_HINTS[question.id] ?? { label: question.variable }}
                initial={answers[question.id]}
                onSubmit={(value) => save(question.id, value)}
              />
            ) : (
              <div className="glass p-6">
                <p className="font-display text-2xl font-semibold">That is everything we need.</p>
                <p className="mt-2 text-muted">Click any assumption on the left to change it.</p>
                <Link to={`/s/${id}/forge`} className="glass mt-4 inline-block px-5 py-3">
                  Build the model
                </Link>
              </div>
            )}
          </div>
        </div>
      </section>
    </>
  );
}