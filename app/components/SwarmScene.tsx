"use client";

import { useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Stars } from "@react-three/drei";
import { AgentPlane } from "./AgentPlane";
import { BlackboardSphere } from "./BlackboardSphere";
import { ConnectionLines } from "./ConnectionLines";
import { SignalParticles } from "./SignalParticle";
import { AGENTS } from "../hooks/useAgentData";
import type { AgentSignal, AgentData } from "../hooks/useAgentData";

function getAgentLayout() {
  const totalAgents = 9;
  const arcSpan = Math.PI * 2;
  const radius = 4.2;

  return AGENTS.map((agent, i) => {
    const angle = (i / totalAgents) * arcSpan;
    const x = Math.sin(angle) * radius;
    const z = Math.cos(angle) * radius;
    const rotY = -angle;

    return {
      ...agent,
      position: [x, 0.2, z] as [number, number, number],
      rotation: [0, rotY, 0] as [number, number, number],
    };
  });
}

interface SceneContentProps {
  agents: AgentData[];
  signals: AgentSignal[];
  liveUrls: Record<number, string | null>;
  isRunning: boolean;
}

function SceneContent({ agents, signals, liveUrls, isRunning }: SceneContentProps) {
  const layout = useMemo(() => getAgentLayout(), []);

  const agentMap = useMemo(() => {
    const map: Record<number, AgentData> = {};
    agents.forEach((a) => {
      map[a.agent_id] = a;
    });
    return map;
  }, [agents]);

  return (
    <>
      <OrbitControls
        makeDefault
        enablePan={false}
        enableZoom={true}
        minDistance={3}
        maxDistance={12}
        minPolarAngle={Math.PI * 0.25}
        maxPolarAngle={Math.PI * 0.6}
        target={[0, 0, -0.5]}
        autoRotate={!isRunning}
        autoRotateSpeed={0.3}
      />

      <ambientLight intensity={0.15} />
      <directionalLight
        position={[5, 5, 5]}
        intensity={0.3}
        color="#334466"
      />

      <Stars
        radius={50}
        depth={80}
        count={3000}
        factor={3}
        saturation={0}
        fade
        speed={0.3}
      />

      <gridHelper
        args={[30, 60, "#0a1628", "#0a1628"]}
        position={[0, -1.2, 0]}
      />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.21, 0]}>
        <planeGeometry args={[30, 30]} />
        <meshBasicMaterial
          color="#020408"
          transparent
          opacity={0.8}
        />
      </mesh>

      <BlackboardSphere isActive={isRunning} />
      <ConnectionLines isActive={isRunning} />

      {layout.map((agentDef, idx) => {
        const agentId = idx + 1; // Agents are 1-9
        const agentData = agentMap[agentId];
        const liveUrl = liveUrls[agentId] || null;
        
        return (
          <AgentPlane
            key={agentDef.id}
            position={agentDef.position}
            rotation={agentDef.rotation}
            agentName={agentDef.name}
            agentColor={agentDef.color}
            agentRole={agentDef.baseRole}
            agentId={agentId}
            status={agentData?.status || "idle"}
            liveUrl={liveUrl}
            isActive={isRunning && !!liveUrl}
          />
        );
      })}

      <SignalParticles signals={signals} />

      <fog attach="fog" args={["#020408", 8, 25]} />
    </>
  );
}

interface SwarmSceneProps {
  agents: AgentData[];
  signals: AgentSignal[];
  liveUrls: Record<number, string | null>;
  isRunning: boolean;
}

export function SwarmScene({ agents, signals, liveUrls, isRunning }: SwarmSceneProps) {
  return (
    <div style={{ position: "absolute", inset: 0, background: "#020408" }}>
      <Canvas
        camera={{
          position: [0, 2.5, 6],
          fov: 55,
          near: 0.1,
          far: 100,
        }}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: "high-performance",
        }}
        dpr={[1, 1.5]}
      >
        <SceneContent
          agents={agents}
          signals={signals}
          liveUrls={liveUrls}
          isRunning={isRunning}
        />
      </Canvas>
    </div>
  );
}
