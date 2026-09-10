import { getBackendUrl } from "../lib/backendUrl";
import type {
  DayResponse,
  DaySummary,
  NutritionCreate,
  NutritionRead,
  NutritionUpdate,
  RecoveryCreate,
  RecoveryRead,
  RecoveryUpdate,
  SleepCreate,
  SleepRead,
  SleepUpdate,
  SymptomCreate,
  SymptomRead,
  SymptomUpdate,
  TrainingCreate,
  TrainingRead,
  TrainingUpdate,
} from "./types";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${getBackendUrl()}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || res.statusText);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

// --- Days --------------------------------------------------------------

export function getDay(date: string): Promise<DayResponse> {
  return request<DayResponse>(`/api/days/${date}`);
}

export function getDaysRange(start: string, end: string): Promise<DaySummary[]> {
  return request<DaySummary[]>(`/api/days?start=${start}&end=${end}`);
}

// --- Training ------------------------------------------------------------

export function createTraining(date: string, payload: TrainingCreate): Promise<TrainingRead> {
  return request(`/api/days/${date}/training`, { method: "POST", body: JSON.stringify(payload) });
}

export function updateTraining(id: number, payload: TrainingUpdate): Promise<TrainingRead> {
  return request(`/api/training/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteTraining(id: number): Promise<void> {
  return request(`/api/training/${id}`, { method: "DELETE" });
}

// --- Sleep -----------------------------------------------------------------

export function createSleep(date: string, payload: SleepCreate): Promise<SleepRead> {
  return request(`/api/days/${date}/sleep`, { method: "POST", body: JSON.stringify(payload) });
}

export function updateSleep(id: number, payload: SleepUpdate): Promise<SleepRead> {
  return request(`/api/sleep/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteSleep(id: number): Promise<void> {
  return request(`/api/sleep/${id}`, { method: "DELETE" });
}

// --- Nutrition ---------------------------------------------------------

export function createNutrition(date: string, payload: NutritionCreate): Promise<NutritionRead> {
  return request(`/api/days/${date}/nutrition`, { method: "POST", body: JSON.stringify(payload) });
}

export function updateNutrition(id: number, payload: NutritionUpdate): Promise<NutritionRead> {
  return request(`/api/nutrition/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteNutrition(id: number): Promise<void> {
  return request(`/api/nutrition/${id}`, { method: "DELETE" });
}

// --- Recovery -----------------------------------------------------------

export function createRecovery(date: string, payload: RecoveryCreate): Promise<RecoveryRead> {
  return request(`/api/days/${date}/recovery`, { method: "POST", body: JSON.stringify(payload) });
}

export function updateRecovery(id: number, payload: RecoveryUpdate): Promise<RecoveryRead> {
  return request(`/api/recovery/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteRecovery(id: number): Promise<void> {
  return request(`/api/recovery/${id}`, { method: "DELETE" });
}

// --- Symptoms ------------------------------------------------------------

export function createSymptom(date: string, payload: SymptomCreate): Promise<SymptomRead> {
  return request(`/api/days/${date}/symptoms`, { method: "POST", body: JSON.stringify(payload) });
}

export function updateSymptom(id: number, payload: SymptomUpdate): Promise<SymptomRead> {
  return request(`/api/symptoms/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function deleteSymptom(id: number): Promise<void> {
  return request(`/api/symptoms/${id}`, { method: "DELETE" });
}
