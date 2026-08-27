export type PostureStatus =
  | "good"
  | "slouching"
  | "leaning"
  | "forward_head";

export type BodyRegion =
  | "spine"
  | "shoulders"
  | "neck"
  | "hips"
  | "overall";

export type WorstHabit =
  | "none"
  | "slouching"
  | "leaning"
  | "forward_head";

export interface LiveTick {
  type: "live";
  posture: PostureStatus;
  severity: number;
  body_region: BodyRegion;
  alert: boolean;
  spoken_cue: string;
  tip: string;
}

export interface Exercise {
  name: string;
  reps: string;
  why: string;
}

export interface SessionSummary {
  type: "summary";
  overall_score: number;
  posture_score: number;
  alignment_score: number;
  time_good_pct: number;
  slouch_events: number;
  worst_habit: WorstHabit;
  strengths: string[];
  improvements: string[];
  exercises: Exercise[];
}

export type CoachingEvent = LiveTick | SessionSummary;

export const SUMMARY_STORAGE_KEY = "posturesense_summary";
