import { useEffect, useRef, useState } from 'react';
import { mockWhatIf, type MockReplyType } from '../api/mockWhatIf';
import type { WhatIfResponse } from '../contracts';

export function WhatIfBar({ parentBranchId }: { parentBranchId: string }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [replyType, setReplyType] = useState<MockReplyType>('param');
  const [busy, setBusy] = useState(false);
  const [reply, setReply] = useState<WhatIfResponse | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((o) => !o);
      } else if (e.key === 'Escape') {
        setOpen(false);
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || busy) return;
    setBusy(true);
    setReply(await mockWhatIf({ parent_branch_id: parentBranchId, text }, replyType));
    setBusy(false);
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="glass fixed bottom-6 left-1/2 -translate-x-1/2 px-5 py-3 print:hidden"
      >
        Ask what if… <span className="text-muted">(⌘K / Ctrl+K)</span>
      </button>

      {open && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Ask what if"
          className="fixed inset-0 z-10 flex items-end justify-center bg-black/60 p-6 print:hidden"
          onClick={() => setOpen(false)}
        >
          <div className="glass w-full max-w-xl bg-void p-5" onClick={(e) => e.stopPropagation()}>
            <p className="font-mono text-xs text-flip">MOCK · replies are fake, nothing is computed</p>
            <form onSubmit={submit} className="mt-3">
              <label htmlFor="whatif" className="sr-only">What if question</label>
              <input
                id="whatif"
                ref={inputRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="What if I leave in 18 months?"
                className="w-full rounded-control bg-white/5 px-3 py-2"
              />
              <div className="mt-3 flex items-center gap-3">
                <label htmlFor="rt" className="text-xs text-muted">Mock reply type</label>
                <select
                  id="rt"
                  value={replyType}
                  onChange={(e) => setReplyType(e.target.value as MockReplyType)}
                  className="rounded-control bg-white/10 px-2 py-1 text-sm"
                >
                  <option value="param">param</option>
                  <option value="structural">structural</option>
                  <option value="out_of_scope">out_of_scope</option>
                </select>
                <button type="submit" disabled={busy} className="glass ml-auto px-4 py-2">
                  {busy ? 'Thinking…' : 'Ask'}
                </button>
              </div>
            </form>

            {reply && (
              <div className="mt-4 text-sm" aria-live="polite">
                <p>{reply.message}</p>
                {reply.type !== 'out_of_scope' && (
                  <p className="mt-1 font-mono text-muted">branch: {reply.branch_id}</p>
                )}
                {reply.suggestions && reply.suggestions.length > 0 && (
                  <ul className="mt-2 list-disc pl-5 text-muted">
                    {reply.suggestions.map((s) => <li key={s}>{s}</li>)}
                  </ul>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}