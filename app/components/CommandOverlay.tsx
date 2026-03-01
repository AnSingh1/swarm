"use client";

import { useState, useRef, useEffect } from "react";
import {
  Search,
  Zap,
  Activity,
  Radio,
  StopCircle,
  RotateCcw,
} from "lucide-react";
import { 
  getAgentById, 
  getLogIcon, 
  type LogEntry 
} from "../hooks/useAgentData";

interface CommandOverlayProps {
  isRunning: boolean;
  logs: LogEntry[];
  activeAgentCount: number;
  onCreateMission: (prompt: string) => void;
  onStopAll: () => void;
  onResetAll: () => void;
}

export function CommandOverlay({
  isRunning,
  logs,
  activeAgentCount,
  onCreateMission,
  onStopAll,
  onResetAll,
}: CommandOverlayProps) {
  const [query, setQuery] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = 0;
    }
  }, [logs]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onCreateMission(query.trim());
    setQuery("");
  };

  return (
    <>
      {/* Top bar */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          right: 0,
          height: 48,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 20px",
          background: "linear-gradient(180deg, rgba(2,4,8,0.95) 0%, rgba(2,4,8,0) 100%)",
          zIndex: 50,
          fontFamily: "'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: isRunning ? "#00f0ff" : "#333",
              boxShadow: isRunning ? "0 0 8px #00f0ff" : "none",
            }}
          />
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: "#00f0ff",
              letterSpacing: 3,
              textTransform: "uppercase",
            }}
          >
            Content Swarm
          </span>
          <span
            style={{
              fontSize: 9,
              color: "#334",
              marginLeft: 8,
              fontWeight: 400,
            }}
          >
            v1.0
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {isRunning && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                fontSize: 10,
                color: "#10b981",
                letterSpacing: 1,
              }}
            >
              <Activity size={10} />
              <span>{activeAgentCount} AGENTS ACTIVE</span>
            </div>
          )}
          <button
            onClick={onResetAll}
            title="Reset All (Delete Everything)"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              padding: "4px 8px",
              background: "transparent",
              border: "1px solid #dc262620",
              borderRadius: 2,
              color: "#dc2626",
              fontSize: 9,
              fontWeight: 600,
              cursor: "pointer",
              transition: "all 0.2s",
              letterSpacing: 1,
              textTransform: "uppercase",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#dc262610";
              e.currentTarget.style.borderColor = "#dc262640";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent";
              e.currentTarget.style.borderColor = "#dc262620";
            }}
          >
            <RotateCcw size={9} />
            Reset
          </button>
          <div
            style={{
              fontSize: 10,
              color: "#334455",
              letterSpacing: 1,
            }}
          >
            {new Date().toLocaleTimeString("en-US", { hour12: false })}
          </div>
        </div>
      </div>

      {/* Signal/Log panel - right side */}
      {logs.length > 0 && (
        <div
          ref={logRef}
          style={{
            position: "fixed",
            top: 56,
            right: 12,
            width: 320,
            maxHeight: "calc(100vh - 160px)",
            overflowY: "auto",
            zIndex: 40,
            fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
            background: "rgba(2,4,8,0.85)",
            backdropFilter: "blur(8px)",
            borderRadius: 4,
            border: "1px solid #141822",
            padding: 12,
          }}
        >
          <div
            style={{
              fontSize: 9,
              color: "#445",
              letterSpacing: 2,
              textTransform: "uppercase",
              marginBottom: 12,
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            <Radio size={8} />
            Swarm Logs
            <span style={{ marginLeft: "auto", color: "#334" }}>
              {logs.length} entries
            </span>
          </div>
          {logs.slice(0, 30).map((log, i) => {
            const agent = getAgentById(log.agent_id);
            return (
              <div
                key={log._id || i}
                style={{
                  fontSize: 9,
                  lineHeight: "16px",
                  padding: "6px 0",
                  borderBottom: "1px solid #0a0e14",
                  opacity: i === 0 ? 1 : Math.max(0.3, 1 - i * 0.05),
                  animation: i === 0 ? "fadeIn 0.3s ease" : "none",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    marginBottom: 3,
                  }}
                >
                  <span
                    style={{
                      padding: "1px 6px",
                      borderRadius: 2,
                      background: `${agent.color}15`,
                      color: agent.color,
                      fontSize: 8,
                      fontWeight: 600,
                      letterSpacing: 0.5,
                    }}
                  >
                    {agent.name}
                  </span>
                  <span style={{ color: "#334", fontSize: 8 }}>
                    {new Date(log.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
                  <span style={{ fontSize: 11 }}>{getLogIcon(log.type)}</span>
                  <span style={{ color: "#889", flex: 1 }}>{log.message}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Bottom command input */}
      <div
        style={{
          position: "fixed",
          bottom: 0,
          left: 0,
          right: 0,
          padding: "16px 20px 20px",
          background: "linear-gradient(0deg, rgba(2,4,8,0.98) 0%, rgba(2,4,8,0.8) 60%, rgba(2,4,8,0) 100%)",
          zIndex: 50,
          fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
        }}
      >
        <div
          style={{
            maxWidth: 680,
            margin: "0 auto",
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          <form
            onSubmit={handleSubmit}
            style={{
              display: "flex",
              gap: 8,
              alignItems: "center",
            }}
          >
            <div
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "10px 12px",
                background: "#080a10",
                border: "1px solid #141822",
                borderRadius: 3,
              }}
            >
              <Search size={14} style={{ color: "#334", flexShrink: 0 }} />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter mission prompt..."
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: "#c8d0e0",
                  fontSize: 12,
                  fontFamily: "inherit",
                  letterSpacing: 0.3,
                }}
              />
            </div>

            <button
              type="submit"
              disabled={!query.trim()}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "10px 16px",
                background: query.trim()
                  ? "linear-gradient(135deg, #00c8ff 0%, #0088cc 100%)"
                  : "#0a0e14",
                border: query.trim()
                  ? "1px solid #00d4ff40"
                  : "1px solid #141822",
                borderRadius: 3,
                color: query.trim() ? "#020408" : "#334",
                fontSize: 11,
                fontWeight: 600,
                fontFamily: "inherit",
                letterSpacing: 1,
                cursor: query.trim() ? "pointer" : "default",
                textTransform: "uppercase",
                transition: "all 0.2s",
              }}
            >
              <Zap size={12} />
              {isRunning ? "New Mission" : "Deploy Swarm"}
            </button>

            {isRunning && (
              <button
                type="button"
                onClick={onStopAll}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "10px 16px",
                  background: "transparent",
                  border: "1px solid #dc262640",
                  borderRadius: 3,
                  color: "#dc2626",
                  fontSize: 11,
                  fontWeight: 600,
                  fontFamily: "inherit",
                  letterSpacing: 1,
                  cursor: "pointer",
                  textTransform: "uppercase",
                  transition: "all 0.2s",
                }}
              >
                <StopCircle size={12} />
                Stop All
              </button>
            )}
          </form>

          {!isRunning && (
            <div
              style={{
                textAlign: "center",
                fontSize: 9,
                color: "#223",
                letterSpacing: 1,
              }}
            >
              Try: &quot;Find trending SaaS marketing videos&quot; or &quot;Top performing fitness content on TikTok&quot;
            </div>
          )}
        </div>
      </div>

      {/* Global styles */}
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #141822; border-radius: 2px; }
      `}</style>
    </>
  );
}
