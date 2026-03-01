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
  
  // Debug logging
  if (latestMission) {
    console.log('Latest mission data:', {
      hasLiveUrl: !!latestMission.liveUrl,
      hasLiveUrl2: !!latestMission.liveUrl2,
      hasLiveUrl3: !!latestMission.liveUrl3,
      liveUrl: latestMission.liveUrl?.substring(0, 50),
      liveUrl2: latestMission.liveUrl2?.substring(0, 50),
      liveUrl3: latestMission.liveUrl3?.substring(0, 50),
    });
  }
  
  // Mutations
  const createMission = useMutation(api.missions.createMission);
  const deleteAllMissions = useMutation(api.missions.deleteAllMissions);
  const deleteAllAgents = useMutation(api.agents.deleteAllAgents);
  const deleteAllDiscoveries = useMutation(api.discoveries.deleteAllDiscoveries);
  
  const handleCreateMission = async () => {
    if (missionPrompt.trim()) {
      await createMission({ prompt: missionPrompt });
      setMissionPrompt("");
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-8">
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

      {/* Livestream View - 3 Streams */}
      {(latestMission?.liveUrl || latestMission?.liveUrl2 || latestMission?.liveUrl3) && (
        <div className="mb-8 p-4 border border-green-600 rounded">
          <h2 className="text-xl font-semibold mb-4 text-green-400">
            🔴 Live TikTok Streams ({[latestMission.liveUrl, latestMission.liveUrl2, latestMission.liveUrl3].filter(Boolean).length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {latestMission.liveUrl && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-green-900">Stream 1</div>
                <iframe
                  src={latestMission.liveUrl}
                  className="w-full h-[500px] border-0"
                  title="Browser Livestream 1"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl2 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-green-900">Stream 2</div>
                <iframe
                  src={latestMission.liveUrl2}
                  className="w-full h-[500px] border-0"
                  title="Browser Livestream 2"
                  allow="autoplay; fullscreen"
                />
              </div>
            )}
            {latestMission.liveUrl3 && (
              <div className="bg-gray-900 rounded overflow-hidden">
                <div className="text-sm font-semibold p-2 bg-green-900">Stream 3</div>
                <iframe
                  src={latestMission.liveUrl3}
                  className="w-full h-[500px] border-0"
                  title="Browser Livestream 3"
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

