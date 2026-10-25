"use client";

/** The LLM judge page: starts a run, follows it live and lists the stored runs. */

import { AdminHeading, AdminLoadState } from "@/components/admin/AdminStates";
import { EvalItemView } from "@/components/admin/judge/EvalItemView";
import { RunReport } from "@/components/admin/judge/RunReport";
import { runHref, RunsTable } from "@/components/admin/judge/RunsTable";
import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { useLanguage } from "@/context/LanguageContext";
import { useAnswerEval, useAnswerEvalRuns, type AnswerEvalError } from "@/hooks/admin/useAnswerEval";
import { useFormatters } from "@/hooks/useFormatters";
import { interpolate } from "@/i18n";
import type { EvalSet } from "@/services/admin";

/** Live items shown while a run streams; the run detail has every one. */
const LIVE_ITEMS = 8;

export default function JudgeClientPage() {
  const { t } = useLanguage();
  const tj = t.admin.judge;
  const f = useFormatters();
  const { state: history, reload } = useAnswerEvalRuns();
  const evaluation = useAnswerEval(reload, tj.leaveConfirm);
  const { running, done, total, items, finished, error } = evaluation;

  const start = (set: EvalSet) => {
    // `aria-disabled`, not `disabled`: the button keeps the focus while it waits
    if (running) return;
    void evaluation.run(set);
  };

  const action = (set: EvalSet, label: string, cost: string) => (
    <div className="flex flex-col items-start gap-1">
      <Button
        type="button"
        size="sm"
        variant={set === "questions" ? "primary" : "secondary"}
        onClick={() => start(set)}
        aria-disabled={running !== null}
        aria-describedby={`judge-cost-${set}`}
        className={running ? "cursor-not-allowed opacity-60" : undefined}
      >
        {running === set ? tj.running : label}
      </Button>
      <span id={`judge-cost-${set}`} className="text-xs text-text-secondary">
        {cost}
      </span>
    </div>
  );

  return (
    <div className="flex flex-col gap-8">
      <div>
        <AdminHeading title={tj.title} subtitle={tj.subtitle}>
          <div className="flex flex-wrap gap-4">
            {action("questions", tj.runQuestions, tj.costQuestions)}
            {action("golden", tj.runGolden, tj.costGolden)}
          </div>
        </AdminHeading>
        <p className="max-w-3xl text-sm text-text-secondary">{tj.explain}</p>
      </div>

      <p role="status" className="sr-only">
        {finished && !running ? interpolate(tj.done, { status: tj.statuses[finished.status] }) : ""}
      </p>

      {error && <RunError error={error} />}

      {running && (
        <section aria-label={tj.live} className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <progress
              aria-label={tj.progressLabel}
              value={done}
              max={total || 1}
              className="h-2 w-full max-w-md accent-accent"
            />
            <span className="text-sm tabular-nums text-text-secondary">
              {interpolate(tj.progress, {
                done: f.formatNumber(done),
                total: total ? f.formatNumber(total) : "…",
              })}
            </span>
          </div>
          <p className="text-sm text-text-secondary">{tj.keepOpen}</p>
          {items.length > 0 && (
            <ul className="flex flex-col gap-4 rounded-xl border border-border-card bg-bg-card p-4">
              {items.slice(0, LIVE_ITEMS).map((item) => (
                <li key={item.key}>
                  <EvalItemView item={item} />
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {finished && !running && (
        <section className="flex flex-col gap-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="font-heading text-lg text-text-primary">{tj.sets[finished.set]}</h2>
            <Link
              href={runHref(finished)}
              className="rounded text-sm text-accent hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
            >
              {tj.openRun}
            </Link>
          </div>
          <RunReport run={finished} items={items} />
        </section>
      )}

      <section className="flex flex-col gap-3">
        <h2 className="font-heading text-lg text-text-primary">{tj.history.title}</h2>
        {history.status === "ready" ? (
          <RunsTable runs={history.runs} />
        ) : (
          <AdminLoadState
            status={history.status}
            error={history.status === "error" ? history.error : undefined}
            onRetry={reload}
          />
        )}
      </section>
    </div>
  );
}

function RunError({ error }: { error: AnswerEvalError }) {
  const { t } = useLanguage();
  const tj = t.admin.judge;
  let message: string;
  if (error.kind === "busy") message = tj.busy;
  else if (error.kind === "cut") message = tj.cut;
  else if (error.kind === "stopped") message = interpolate(tj.stopped, { message: error.message });
  else return <AdminLoadState status="error" error={error.kind} />;
  return (
    <p role="alert" className="rounded-xl border border-border-card bg-bg-card p-4 text-sm text-error">
      {message}
    </p>
  );
}
