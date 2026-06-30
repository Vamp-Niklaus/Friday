import axios from "axios";
import { supabase } from "./supabase";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  return config;
});

export interface Task {
  id: string;
  title: string;
  notes: string | null;
  status: "open" | "completed";
  todo_at: string;
  reminder_start_at: string;
  timezone: string;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  metadata: Record<string, unknown>;
  formatted_date?: string;
}

export interface TaskGroup {
  date: string;
  tasks: Task[];
}

export interface TaskGroupResponse {
  groups: TaskGroup[];
}

export interface ChatResponse {
  message: string;
  task_created: boolean;
  task: Task | null;
  needs_follow_up: boolean;
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>("/v1/chat/", { message });
  return response.data;
}

export async function getChatHistory(limit: number = 20, offset: number = 0): Promise<{ messages: { role: "user" | "assistant"; content: string }[] }> {
  const response = await api.get(`/v1/chat/history?limit=${limit}&offset=${offset}`);
  return response.data;
}

export async function listOpenTodos(): Promise<TaskGroupResponse> {
  const response = await api.get<TaskGroupResponse>("/v1/todos/open");
  return response.data;
}

export async function listHistoryTodos(): Promise<TaskGroupResponse> {
  const response = await api.get<TaskGroupResponse>("/v1/todos/history");
  return response.data;
}

export async function updateTaskTitle(taskId: string, title: string): Promise<Task> {
  const response = await api.patch<Task>(`/v1/todos/${taskId}`, { title });
  return response.data;
}

export async function completeTask(taskId: string): Promise<Task> {
  const response = await api.post<Task>(`/v1/todos/${taskId}/complete`);
  return response.data;
}

export interface ProblemQueueResponse {
  daily_quota: number;
  days_since_start: number;
  expected_completed: number;
  actual_completed: number;
  due_today_count: number;
  past_due: Task[];
  due_today: Task[];
  upcoming: Task[];
  solved_today: Task[];
}

export async function getProblemQueue(): Promise<ProblemQueueResponse> {
  const res = await api.get<ProblemQueueResponse>("/v1/problems/queue");
  return res.data;
}

export async function updateQueueSettings(dailyQuota: number): Promise<void> {
  await api.patch("/v1/problems/settings", { daily_quota: dailyQuota });
}

export async function getCompletedProblems(): Promise<{ completed: Task[] }> {
  const res = await api.get<{ completed: Task[] }>("/v1/problems/completed");
  return res.data;
}

export async function reviseProblem(taskId: string): Promise<Task> {
  const response = await api.post<Task>(`/v1/problems/${taskId}/revise`);
  return response.data;
}

export async function deleteTask(taskId: string): Promise<void> {
  await api.delete(`/v1/todos/${taskId}`);
}
