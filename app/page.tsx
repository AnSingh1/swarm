"use client";

import { useState } from "react";
import { useQuery, useMutation } from "convex/react";
import { api } from "../convex/_generated/api";

export default function Home() {
  const [missionPrompt, setMissionPrompt] = useState("");
  
  // Queries
  const latestMission = useQuery(api.missions.getLatestMission);
  const allAgents = useQuery(api.agents.getAllAgents);
  const discoveries = useQuery(api.discoveries.getDiscoveries);
  // @ts-ignore - logs API will be available after running `npx convex dev`
  const recentLogs = useQuery(api.logs?.getRecentLogs, { limit: 50 });
  
  // Debug logging
  if (latestMission) {
    console.log('Latest mission data:', {
      hasLiveUrl: !!latestMission.liveUrl,
      hasLiveUrl2: !!latestMission.liveUrl2,
      hasLiveUrl3: !!latestMission.liveUrl3,
      hasLiveUrl4: !!latestMission.liveUrl4,
      hasLiveUrl5: !!latestMission.liveUrl5,
      hasLiveUrl6: !!latestMission.liveUrl6,
      hasLiveUrl7: !!latestMission.liveUrl7,
      hasLiveUrl8: !!latestMission.liveUrl8,
      hasLiveUrl9: !!latestMission.liveUrl9,
    });
  }
  
  // Mutations
  const createMission = useMutation(api.missions.createMission);
  const deleteAllMissions = useMutation(api.missions.deleteAllMissions);
  const deleteAllAgents = useMutation(api.agents.deleteAllAgents);
  const deleteAllDiscoveries = useMutation(api.discoveries.deleteAllDiscoveries);
  // @ts-ignore - control API will be available after running `npx convex dev`
  const sendCommand = useMutation(api.control?.sendCommand);
  
  const handleCreateMission = async () => {
    if (missionPrompt.trim()) {
      await createMission({ prompt: missionPrompt });
      setMissionPrompt("");
    }
  };

  const handleStopAllSessions = async () => {
    if (confirm("⚠️ Stop all browser sessions? This will terminate all 9 agents.")) {
      await sendCommand({ command: "stop_all" });
      alert("✅ Stop command sent! Agents will shut down gracefully.");
    }
  };

  // Helper functions for log formatting
  const getAgentColor = (agentId: number) => {
    if (agentId === 0) return "text-gray-400"; // Swarm manager
    if (agentId <= 3) return "text-blue-400";   // TikTok (agents 1-3)
    if (agentId <= 6) return "text-red-400";    // YouTube (agents 4-6)
    return "text-purple-400";                    // DuckDuckGo (agents 7-9)
  };

  const getAgentBadgeColor = (agentId: number) => {
    if (agentId === 0) return "bg-gray-700 text-gray-300";
    if (agentId <= 3) return "bg-blue-900 text-blue-300";
    if (agentId <= 6) return "bg-red-900 text-red-300";
    return "bg-purple-900 text-purple-300";
  };

  const getAgentPlatform = (agentId: number) => {
    if (agentId === 0) return "🧠 Swarm";
    if (agentId <= 3) return "🔵 TikTok";
    if (agentId <= 6) return "🔴 YouTube";
    return "🟣 DuckDuckGo";
  };

  const getLogIcon = (type: string) => {
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
  };

  return (
    <div className="min-h-screen bg-black text-white p-8">
      {/* Fixed Log Panel - Top Right */}
      <div className="fixed top-4 right-4 w-96 max-h-[600px] bg-gray-900 border border-gray-700 rounded-lg shadow-2xl overflow-hidden z-50">
        <div className="bg-gray-800 px-4 py-3 border-b border-gray-700 sticky top-0">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            📊 Swarm Logs
            <span className="text-xs font-normal text-gray-400">
              (Live)
            </span>
          </h3>
        </div>
        <div className="overflow-y-auto max-h-[540px] p-3 space-y-2">
          {recentLogs && recentLogs.length > 0 ? (
            recentLogs.map((log: any) => (
              <div
                key={log._id}
                className={`text-xs p-2 rounded ${getAgentColor(log.agent_id)} bg-gray-800 border border-gray-700`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${getAgentBadgeColor(log.agent_id)}`}>
                    {getAgentPlatform(log.agent_id)} {log.agent_id > 0 ? log.agent_id : ""}
                  </span>
                  <span className="text-[10px] text-gray-500">
                    {new Date(log.timestamp * 1000).toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex items-start gap-1.5">
                  <span className="text-sm">{getLogIcon(log.type)}</span>
                  <span className="flex-1 leading-snug">{log.message}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-gray-500 py-8">
              No logs yet. Start a mission to see agent activity.
            </div>
          )}
        </div>
      </div>

      <h1 className="text-4xl font-bold mb-8">SwarmCast Debug UI</h1>
      
      {/* Mission Input */}
      <div className="mb-8 p-4 border border-gray-700 rounded">
        <h2 className="text-xl font-semibold mb-4">Create New Mission</h2>
        <div className="flex gap-2">
          <input
            type="text"
            value={missionPrompt}
            onChange={(e) => setMissionPrompt(e.target.value)}
            placeholder="Enter mission prompt..."
            className="flex-1 px-4 py-2 bg-gray-900 border border-gray-700 rounded text-white"
            onKeyDown={(e) => e.key === "Enter" && handleCreateMission()}
          />
          <button
            onClick={handleCreateMission}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold"
          >
            Create Mission
          </button>
        </div>
      </div>

      {/* Livestream View - 9 Streams (3 TikTok + 3 YouTube + 3 DuckDuckGo) */}
      {(latestMission?.liveUrl || latestMission?.liveUrl2 || latestMission?.liveUrl3 || latestMission?.liveUrl4 || latestMission?.liveUrl5 || latestMission?.liveUrl6 || latestMission?.liveUrl7 || latestMission?.liveUrl8 || latestMission?.liveUrl9) && (
        <div className="mb-8 p-4 border border-green-600 rounded">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-semibold text-green-400">
                🔴 Live Streams ({[latestMission.liveUrl, latestMission.liveUrl2, latestMission.liveUrl3, latestMission.liveUrl4, latestMission.liveUrl5, latestMission.liveUrl6, latestMission.liveUrl7, latestMission.liveUrl8, latestMission.liveUrl9].filter(Boolean).length})
              </h2>
              <div className="text-sm text-gray-400">3 TikTok + 3 YouTube + 3 DuckDuckGo</div>
            </div>
            <button
              onClick={handleStopAllSessions}
              className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded font-bold text-white shadow-lg hover:shadow-xl transition-all"
            >
              🛑 Stop All Sessions
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {latestMission.liveUrl && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-blue-900">TikTok 1</div>
                <iframe
                  src={latestMission.liveUrl}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 1"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl2 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-blue-900">TikTok 2</div>
                <iframe
                  src={latestMission.liveUrl2}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 2"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl3 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-blue-900">TikTok 3</div>
                <iframe
                  src={latestMission.liveUrl3}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 3"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl4 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-red-900">YouTube 1</div>
                <iframe
                  src={latestMission.liveUrl4}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 4"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl5 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-red-900">YouTube 2</div>
                <iframe
                  src={latestMission.liveUrl5}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 5"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl6 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-red-900">YouTube 3</div>
                <iframe
                  src={latestMission.liveUrl6}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 6"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl7 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-purple-900">DuckDuckGo 1</div>
                <iframe
                  src={latestMission.liveUrl7}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 7"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl8 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-purple-900">DuckDuckGo 2</div>
                <iframe
                  src={latestMission.liveUrl8}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 8"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl9 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-purple-900">DuckDuckGo 3</div>
                <iframe
                  src={latestMission.liveUrl9}
                  className="w-full h-[400px] border-0"
                  title="Browser Livestream 9"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
          </div>
          {latestMission.shareUrl && (
            <div className="mt-2 text-sm text-gray-400">
              Share URL: <a href={latestMission.shareUrl} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">{latestMission.shareUrl}</a>
            </div>
          )}
        </div>
      )}

      {/* Add CSS to hide everything except screencast_viewer */}
      <style jsx global>{`
        iframe {
          pointer-events: none;
        }
        iframe body > *:not(.screencast_viewer) {
          display: none !important;
        }
      `}</style>

      {/* Three Column Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Current Mission */}
        <div className="border border-yellow-600 rounded p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-yellow-400">Current Mission</h2>
            <button
              onClick={() => deleteAllMissions()}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm font-semibold"
              disabled={!latestMission}
            >
              Delete All
            </button>
          </div>
          <div className="bg-gray-900 p-3 rounded overflow-auto max-h-96">
            <pre className="text-xs text-green-400 whitespace-pre-wrap">
              {latestMission === undefined 
                ? "Loading..." 
                : latestMission === null 
                ? "No mission yet" 
                : JSON.stringify(latestMission, null, 2)}
            </pre>
          </div>
        </div>

        {/* Live Agent States */}
        <div className="border border-purple-600 rounded p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-purple-400">
              Live Agent States ({allAgents?.length ?? 0})
            </h2>
            <button
              onClick={() => deleteAllAgents()}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm font-semibold"
              disabled={!allAgents || allAgents.length === 0}
            >
              Delete All
            </button>
          </div>
          <div className="bg-gray-900 p-3 rounded overflow-auto max-h-96">
            <pre className="text-xs text-green-400 whitespace-pre-wrap">
              {allAgents === undefined 
                ? "Loading..." 
                : allAgents.length === 0 
                ? "No agents yet" 
                : JSON.stringify(allAgents, null, 2)}
            </pre>
          </div>
        </div>

        {/* Latest Discoveries */}
        <div className="border border-cyan-600 rounded p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold text-cyan-400">
              Latest Discoveries ({discoveries?.length ?? 0})
            </h2>
            <button
              onClick={() => deleteAllDiscoveries()}
              className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm font-semibold"
              disabled={!discoveries || discoveries.length === 0}
            >
              Delete All
            </button>
          </div>
          <div className="bg-gray-900 p-3 rounded overflow-auto max-h-96">
            <pre className="text-xs text-green-400 whitespace-pre-wrap">
              {discoveries === undefined 
                ? "Loading..." 
                : discoveries.length === 0 
                ? "No discoveries yet" 
                : JSON.stringify(discoveries, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

