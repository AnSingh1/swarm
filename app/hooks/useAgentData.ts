"use client";

// Agent definitions for 9 agents (3 TikTok + 3 YouTube + 3 DuckDuckGo)
export const AGENTS = [
  { id: "tiktok-1", agentId: 1, name: "Vibe", color: "#00f2ea", baseRole: "Discovery", platform: "tiktok" },
  { id: "tiktok-2", agentId: 2, name: "Pulse", color: "#00d4e0", baseRole: "Collection", platform: "tiktok" },
  { id: "tiktok-3", agentId: 3, name: "Rhythm", color: "#00b6d6", baseRole: "Analysis", platform: "tiktok" },
  { id: "youtube-1", agentId: 4, name: "Echo", color: "#ff0033", baseRole: "Discovery", platform: "youtube" },
  { id: "youtube-2", agentId: 5, name: "Nova", color: "#e6002e", baseRole: "Collection", platform: "youtube" },
  { id: "youtube-3", agentId: 6, name: "Blaze", color: "#cc0029", baseRole: "Analysis", platform: "youtube" },
  { id: "ddg-1", agentId: 7, name: "Cipher", color: "#a855f7", baseRole: "Discovery", platform: "duckduckgo" },
  { id: "ddg-2", agentId: 8, name: "Nexus", color: "#9333ea", baseRole: "Collection", platform: "duckduckgo" },
  { id: "ddg-3", agentId: 9, name: "Oracle", color: "#7c3aed", baseRole: "Analysis", platform: "duckduckgo" },
] as const;

export type AgentId = (typeof AGENTS)[number]["id"];

export interface AgentData {
  _id: string;
  agent_id: number;
  status: "idle" | "searching" | "found_trend" | "weak" | "reassigning" | "exploiting";
  current_url: string;
  profile_id: string;
  energy: number;
}

export interface AgentSignal {
  _id: string;
  fromAgent: number;
  toAgent: number;
  message: string;
  signalType: string;
  timestamp: number;
}

export interface LogEntry {
  _id: string;
  agent_id: number;
  message: string;
  type: "search" | "analysis" | "likes" | "discovery" | "energy_gain" | "energy_loss" | "task_swap" | "status" | "error";
  timestamp: number;
  metadata?: string;
}

export interface DiscoveredContent {
  _id: string;
  video_url: string;
  thumbnail: string;
  found_by_agent_id: number;
  keywords?: string;
  likes?: number;
  views?: number;
  comments?: number;
}

export const PLATFORM_COLORS: Record<string, string> = {
  youtube: "#ff0033",
  tiktok: "#00f2ea",
  duckduckgo: "#a855f7",
  twitter: "#1d9bf0",
  linkedin: "#0a66c2",
  instagram: "#e4405f",
  blog: "#10b981",
};

// Helper to get agent info by agent_id
export function getAgentById(agentId: number) {
  return AGENTS.find(a => a.agentId === agentId) || AGENTS[0];
}

// Helper to get agent color by agent_id
export function getAgentColor(agentId: number): string {
  const agent = getAgentById(agentId);
  return agent?.color || "#666";
}

// Helper to get agent platform badge
export function getAgentPlatform(agentId: number): string {
  if (agentId === 0) return "🧠 Swarm";
  if (agentId <= 3) return "🔵 TikTok";
  if (agentId <= 6) return "🔴 YouTube";
  return "🟣 DuckDuckGo";
}

// Helper to get log icon
export function getLogIcon(type: string): string {
  switch(type) {
    case "search": return "🔍";
    case "analysis": return "📹";
    case "likes": return "💖";
    case "discovery": return "✨";
    case "energy_gain": return "⚡️";
    case "energy_loss": return "🔋";
    case "task_swap": return "🔄";
    case "status": return "📊";
    case "error": return "❌";
    default: return "📝";
  }
}

// Helper to get badge color classes
export function getAgentBadgeColor(agentId: number): string {
  if (agentId === 0) return "bg-gray-700 text-gray-300";
  if (agentId <= 3) return "bg-cyan-900/50 text-cyan-300";
  if (agentId <= 6) return "bg-red-900/50 text-red-300";
  return "bg-purple-900/50 text-purple-300";
}

// Convert logs to signals for the 3D visualization
export function logsToSignals(logs: LogEntry[]): AgentSignal[] {
  return logs
    .filter(log => log.agent_id > 0)
    .slice(0, 20)
    .map((log, idx) => ({
      _id: log._id || `signal_${idx}`,
      fromAgent: log.agent_id,
      toAgent: log.agent_id === 9 ? 1 : log.agent_id + 1, // Chain to next agent
      message: log.message,
      signalType: log.type,
      timestamp: log.timestamp,
    }));
}
