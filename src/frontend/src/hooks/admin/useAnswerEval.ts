"use client";

/** The LLM judge's runs: one started from the page, streamed, and the stored history. */

import { useCallback, useEffect, useRef, useState } from "react";
import {
  listAnswerEvals,
  streamAnswerEval,
  type EvalItem,
  type EvalRun,
  type EvalSet,
} from "@/services/admin";
import { ApiError, isAbortError } from "@/services/http";
import { toAdminError, type AdminError } from "./adminErrors";

/** What a run can fail with: an admin error, another run in progress, or a stop mid-stream. */
export type AnswerEvalError =
  | { kind: AdminError }
  | { kind: "busy" }
  | { kind: "stopped"; message: string };

export interface AnswerEvalState {
  /** The set being run; `null` when nothing runs. */
  running: EvalSet | null;
  done: number;
  total: number;
  /** The items of the run in progress, newest first. */
  items: EvalItem[];
  /** The run that just finished, as stored. */
  finished: EvalRun | null;
  error: AnswerEvalError | null;
}

const IDLE: AnswerEvalState = {
  running: null,
  done: 0,
  total: 0,
  items: [],
  finished: null,
  error: null,
};

/**
 * Starts a run and follows its stream. Nothing runs until `run()`: a run spends model tokens.
 * Leaving the page aborts the stream; ai_api keeps the run as far as it got.
 * `onFinished` is called when a run ends, finished or not, so the history can reload.
 */
export function useAnswerEval(onFinished?: () => void) {
  const [state, setState] = useState<AnswerEvalState>(IDLE);
  const inFlight = useRef<AbortController | null>(null);
  const finishedRef = useRef(onFinished);

  useEffect(() => {
    finishedRef.current = onFinished;
  });
  useEffect(() => () => inFlight.current?.abort(), []);

  const run = useCallback(async (set: EvalSet) => {
    if (inFlight.current) return;
    const controller = new AbortController();
    inFlight.current = controller;
    setState({ ...IDLE, running: set });
    try {
      for await (const event of streamAnswerEval(set, { signal: controller.signal })) {
        if (event.type === "progress") {
          setState((s) => ({
            ...s,
            done: event.done,
            total: event.total,
            items: [event.item, ...s.items],
          }));
        } else if (event.type === "report") {
          setState((s) => ({ ...s, finished: event.run }));
        } else {
          setState((s) => ({ ...s, error: { kind: "stopped", message: event.error } }));
        }
      }
    } catch (err: unknown) {
      if (controller.signal.aborted || isAbortError(err)) return;
      if (err instanceof ApiError && err.status === 409) {
        setState((s) => ({ ...s, error: { kind: "busy" } }));
      } else {
        const error = toAdminError(err);
        if (error) setState((s) => ({ ...s, error: { kind: error } }));
      }
    } finally {
      if (inFlight.current === controller) inFlight.current = null;
      if (!controller.signal.aborted) {
        setState((s) => ({ ...s, running: null }));
        finishedRef.current?.();
      }
    }
  }, []);

  return { ...state, run };
}

export type RunsState =
  | { status: "loading" }
  | { status: "ready"; runs: EvalRun[] }
  | { status: "error"; error: AdminError };

/** The latest stored runs, newest first; `reload()` asks again and keeps the list meanwhile. */
export function useAnswerEvalRuns() {
  const [state, setState] = useState<RunsState>({ status: "loading" });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    listAnswerEvals({ signal: controller.signal })
      .then((page) => {
        if (!controller.signal.aborted) setState({ status: "ready", runs: page.items });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || isAbortError(err)) return;
        const error = toAdminError(err);
        if (error) setState({ status: "error", error });
      });
    return () => controller.abort();
  }, [version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return { state, reload };
}
