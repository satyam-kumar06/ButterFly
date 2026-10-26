import { fieldLabel, needsCheck, type TermView } from '../lib/terms';

type Props = {
  term: TermView;
  onChange: (value: string) => void;
  onConfirm: () => void;
};

export function TermCard({ term, onChange, onConfirm }: Props) {
  const check = needsCheck(term);
  const id = `term-${term.option_id}-${term.field}`;
  return (
    <li className={`glass p-4 ${check ? 'outline outline-2 outline-flip' : ''}`}>
      <div className="flex items-center justify-between gap-2">
        <label htmlFor={id} className="text-sm text-muted">{fieldLabel(term.field)}</label>
        {check && (
          <span className="rounded-full bg-flip/20 px-2 py-0.5 text-xs text-flip">check this</span>
        )}
      </div>
      <input
        id={id}
        value={String(term.value ?? '')}
        onChange={(e) => onChange(e.target.value)}
        className="mt-2 w-full rounded-control bg-white/5 px-3 py-2 font-mono"
      />
      {term.evidence && (
        <p className="mt-2 text-xs text-muted">
          p.{term.evidence.page}: “{term.evidence.quote}”
        </p>
      )}
      <button type="button" onClick={onConfirm} className="mt-3 text-sm underline">
        {term.confirmed ? 'Confirmed ✓' : 'Mark as correct'}
      </button>
    </li>
  );
}