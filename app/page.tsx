"use client";

import { useState, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";
import { useQuery, useMutation } from "convex/react";
import { api } from "../convex/_generated/api";
import { ResizablePane } from "./components/ResizablePane";
import { ContentWhiteboard } from "./components/ContentWhiteboard";
import { CommandOverlay } from "./components/CommandOverlay";
import { type DiscoveredContent, type LogEntry, type AgentData, type AgentSignal } from "./hooks/useAgentData";

// Dynamically import SwarmScene to avoid SSR issues with Three.js
const SwarmScene = dynamic(
  () => import("./components/SwarmScene").then((mod) => mod.SwarmScene),
  {
    ssr: false,
    loading: () => (
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "#020408",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 16,
          }}
        >
          <div
            style={{
              width: 24,
              height: 24,
              border: "2px solid #141822",
              borderTopColor: "#00f0ff",
              borderRadius: "50%",
              animation: "spin 0.8s linear infinite",
            }}
          />
          <span
            style={{
              fontSize: 10,
              color: "#334",
              letterSpacing: 3,
              textTransform: "uppercase",
            }}
          >
            Initializing Command Center
          </span>
          <style>{`
            @keyframes spin {
              to { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      </div>
    ),
  }
);

export default function Home() {
  const [missionPrompt, setMissionPrompt] = useState("");
  
  // Queries
  const latestMission = useQuery(api.missions.getLatestMission);
  const allAgents = useQuery(api.agents.getAllAgents) as AgentData[] | undefined;
  const discoveries = useQuery(api.discoveries.getDiscoveries) as DiscoveredContent[] | undefined;
  const recentLogs = useQuery(api.logs.getRecentLogs, { limit: 50 }) as LogEntry[] | undefined;
  const recentSignals = useQuery(api.signals.getRecentSignals, { limit: 50 });
  
  // Mutations
  const createMission = useMutation(api.missions.createMission);
  const sendCommand = useMutation(api.control.sendCommand);
  const resetAll = useMutation(api.cleanup.resetAll);

  // Determine if swarm is running
  const isRunning = useMemo(() => {
    if (!latestMission) return false;
    return !!(
      latestMission.liveUrl ||
      latestMission.liveUrl2 ||
      latestMission.liveUrl3 ||
      latestMission.liveUrl4 ||
      latestMission.liveUrl5 ||
      latestMission.liveUrl6 ||
      latestMission.liveUrl7 ||
      latestMission.liveUrl8 ||
      latestMission.liveUrl9
    );
  }, [latestMission]);

  // Build live URLs map for agents
  const liveUrls = useMemo(() => {
    if (!latestMission) return {};
    return {
      1: latestMission.liveUrl || null,
      2: latestMission.liveUrl2 || null,
      3: latestMission.liveUrl3 || null,
      4: latestMission.liveUrl4 || null,
      5: latestMission.liveUrl5 || null,
      6: latestMission.liveUrl6 || null,
      7: latestMission.liveUrl7 || null,
      8: latestMission.liveUrl8 || null,
      9: latestMission.liveUrl9 || null,
    } as Record<number, string | null>;
  }, [latestMission]);

  // Count active agents
  const activeAgentCount = useMemo(() => {
    return Object.values(liveUrls).filter(Boolean).length;
  }, [liveUrls]);

  // Use actual signals from database (orbs)
  const signals = useMemo(() => {
    return (recentSignals || []) as AgentSignal[];
  }, [recentSignals]);

  // Handlers
  const handleCreateMission = useCallback(async (prompt: string) => {
    if (prompt.trim()) {
      await createMission({ prompt });
      setMissionPrompt("");
    }
  }, [createMission]);

  const handleStopAll = useCallback(async () => {
    if (confirm("⚠️ Stop all browser sessions? This will terminate all 9 agents.")) {
      await sendCommand({ command: "stop_all" });
    }
  }, [sendCommand]);

  const handleResetAll = useCallback(async () => {
    if (confirm("⚠️ RESET ALL? This will:\n- Stop all browser sessions\n- Delete all missions\n- Delete all agents\n- Delete all discoveries\n- Delete all logs\n\nThis action cannot be undone!")) {
      await resetAll();
    }
  }, [resetAll]);

  return (
    <div style={{ position: "fixed", inset: 0, overflow: "hidden", background: "#020408" }}>
      <ResizablePane
        defaultWidth={520}
        minWidth={320}
        maxWidth={960}
        left={
          <ContentWhiteboard
            content={discoveries || []}
            isRunning={isRunning}
          />
        }
        right={
          <div style={{ position: "relative", width: "100%", height: "100%" }}>
            <SwarmScene
              agents={allAgents || []}
              signals={signals}
              liveUrls={liveUrls}
              isRunning={isRunning}
            />
          </div>
        }
      />

      {/* Command overlay sits on top of everything */}
      <CommandOverlay
        isRunning={isRunning}
        logs={recentLogs || []}
        activeAgentCount={activeAgentCount}
        onCreateMission={handleCreateMission}
        onStopAll={handleStopAll}
        onResetAll={handleResetAll}
      />
    </div>
  );
}

