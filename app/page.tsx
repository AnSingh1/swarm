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
  
  // Mutations
  const createMission = useMutation(api.missions.createMission);
  
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

      {/* Three Column Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Current Mission */}
        <div className="border border-yellow-600 rounded p-4">
          <h2 className="text-xl font-bold mb-4 text-yellow-400">Current Mission</h2>
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
          <h2 className="text-xl font-bold mb-4 text-purple-400">
            Live Agent States ({allAgents?.length ?? 0})
          </h2>
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
          <h2 className="text-xl font-bold mb-4 text-cyan-400">
            Latest Discoveries ({discoveries?.length ?? 0})
          </h2>
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

