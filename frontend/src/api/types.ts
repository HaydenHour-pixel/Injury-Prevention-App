/**
 * Types mirroring the backend's Pydantic schemas (backend/app/schemas/*.py).
 * Keep field names and nullability exactly in sync with those files — this
 * file has no build-time link to them, so a backend schema change won't
 * surface here as a type error.
 *
 * Absent-vs-logged is load-bearing (spec.md section 4): `null` and `[]` are
 * real, distinct values meaning "never logged". Nothing in this file may
 * default them away.
 */

export type TrainingSource = "strava" | "manual";
export type NutritionSource = "umass_dining_menu" | "manual_food_entry";
export type RecoveryMethodType =
  | "none"
  | "foam_roll"
  | "yoga"
  | "ice_bath"
  | "massage"
  | "stretching"
  | "rest";
export type PainType = "none" | "muscle_soreness" | "dull_ache" | "sharp_pain";
export type PainOnset = "sudden" | "gradual" | "unknown";
export type TrainingPhase = "base" | "build" | "peak" | "taper" | "recovery" | "off";

export interface TrainingRead {
  id: number;
  daily_entry_id: number;
  date: string;
  mileage: number | null;
  intensity_1_to_10: number | null;
  intensity_factor: number | null;
  elevation_gain_ft: number | null;
  notes: string | null;
  source: string | null;
  source_confidence: number | null;
  recall_confidence: number | null;
  created_at: string;
}

export interface TrainingCreate {
  mileage?: number | null;
  intensity_1_to_10?: number | null;
  elevation_gain_ft?: number | null;
  notes?: string | null;
  source?: TrainingSource;
}

export type TrainingUpdate = Partial<TrainingCreate>;

export interface SleepRead {
  id: number;
  daily_entry_id: number;
  date: string;
  hours: number | null;
  quality_1_to_10: number | null;
  bedtime: string | null;
  wake_time: string | null;
  is_nap: boolean;
  source: string | null;
  source_confidence: number | null;
  recall_confidence: number | null;
  created_at: string;
}

export interface SleepCreate {
  hours?: number | null;
  quality_1_to_10?: number | null;
  bedtime?: string | null;
  wake_time?: string | null;
  is_nap?: boolean;
}

export type SleepUpdate = Partial<SleepCreate>;

export interface NutritionRead {
  id: number;
  daily_entry_id: number;
  date: string;
  protein_g: number | null;
  carbs_g: number | null;
  fat_g: number | null;
  calories: number | null;
  training_phase: string | null;
  training_load: number | null;
  meals: unknown | null;
  source: string | null;
  source_confidence: number | null;
  recall_confidence: number | null;
  created_at: string;
}

export interface NutritionCreate {
  protein_g?: number | null;
  carbs_g?: number | null;
  fat_g?: number | null;
  calories?: number | null;
  training_phase?: TrainingPhase | null;
  training_load?: number | null;
  meals?: unknown | null;
  source?: NutritionSource;
}

export type NutritionUpdate = Partial<NutritionCreate>;

export interface RecoveryRead {
  id: number;
  daily_entry_id: number;
  date: string;
  method_type: string;
  duration_minutes: number | null;
  intensity_1_to_10: number | null;
  applied_at: string | null;
  symptom_id: number | null;
  source_confidence: number | null;
  recall_confidence: number | null;
  created_at: string;
}

export interface RecoveryCreate {
  method_type: RecoveryMethodType;
  duration_minutes?: number | null;
  intensity_1_to_10?: number | null;
  applied_at?: string | null;
  symptom_id?: number | null;
}

export type RecoveryUpdate = Partial<RecoveryCreate>;

export interface SymptomRead {
  id: number;
  daily_entry_id: number | null;
  date: string;
  body_location: string;
  intensity_1_to_10: number;
  type: string;
  onset: string | null;
  limiting: boolean;
  description: string | null;
  active: boolean;
  pain_profile_id: number | null;
  source_confidence: number | null;
  recall_confidence: number | null;
  created_at: string;
}

export interface SymptomCreate {
  body_location: string;
  intensity_1_to_10: number;
  type: PainType;
  onset?: PainOnset | null;
  limiting?: boolean;
  description?: string | null;
  active?: boolean;
  pain_profile_id?: number | null;
}

export type SymptomUpdate = Partial<SymptomCreate>;

export interface Completeness {
  training: boolean;
  sleep: boolean;
  nutrition: boolean;
  recovery: boolean;
  symptoms: boolean;
}

export interface DayResponse {
  date: string;
  daily_entry_exists: boolean;
  training: TrainingRead[];
  sleep: SleepRead[];
  nutrition: NutritionRead | null;
  recovery: RecoveryRead[];
  symptoms: SymptomRead[];
  completeness: Completeness;
}

export interface DaySummary {
  date: string;
  daily_entry_exists: boolean;
  completeness: Completeness;
}
