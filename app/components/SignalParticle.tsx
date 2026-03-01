"use client";

import { useRef, useState, useEffect } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { AgentSignal } from "../hooks/useAgentData";
import { AGENTS } from "../hooks/useAgentData";

function getAgentPosition(index: number): THREE.Vector3 {
  const totalAgents = 9;
  const arcSpan = Math.PI * 2;
  const angle = (index / totalAgents) * arcSpan;
  const radius = 4.2;
  return new THREE.Vector3(
    Math.sin(angle) * radius,
    0.2,
    Math.cos(angle) * radius
  );
}

const BLACKBOARD_POS = new THREE.Vector3(0, 0, 0);

interface ActiveParticle {
  id: string;
  fromPos: THREE.Vector3;
  toPos: THREE.Vector3;
  color: string;
  phase: "to_center" | "from_center";
  progress: number;
  message: string;
}

export function SignalParticles({ signals }: { signals: AgentSignal[] }) {
  const [particles, setParticles] = useState<ActiveParticle[]>([]);
  const processedRef = useRef(new Set<string>());

  useEffect(() => {
    if (signals.length === 0) return;
    const latest = signals[0];
    if (processedRef.current.has(latest._id)) return;
    processedRef.current.add(latest._id);

    const id = latest._id;
    
    // Handle two cases:
    // 1. fromAgent=X, toAgent=0: Log event - agent X sends orb to center
    // 2. fromAgent=0, toAgent=X: Broadcast - center sends orb to agent X (discovery)
    
    if (latest.fromAgent === 0 && latest.toAgent > 0) {
      // Broadcast from center to specific agent
      const toIdx = latest.toAgent - 1;
      if (toIdx < 0 || toIdx >= AGENTS.length) return;
      
      const toAgent = AGENTS[toIdx];
      
      setParticles((prev) => [
        ...prev,
        {
          id: `${id}_broadcast`,
          fromPos: BLACKBOARD_POS.clone(),
          toPos: getAgentPosition(toIdx),
          color: "#ffcc00", // Gold color for discoveries
          phase: "from_center",
          progress: 0,
          message: latest.message,
        },
      ]);
    } else if (latest.fromAgent > 0 && latest.toAgent === 0) {
      // Normal log - agent sends to center
      const fromIdx = latest.fromAgent - 1;
      if (fromIdx < 0 || fromIdx >= AGENTS.length) return;
      
      const fromAgent = AGENTS[fromIdx];
      
      setParticles((prev) => [
        ...prev,
        {
          id: `${id}_log`,
          fromPos: getAgentPosition(fromIdx),
          toPos: BLACKBOARD_POS.clone(),
          color: fromAgent.color,
          phase: "to_center",
          progress: 0,
          message: latest.message,
        },
      ]);
    }
  }, [signals]);

  useEffect(() => {
    const interval = setInterval(() => {
      setParticles((prev) => prev.filter((p) => p.progress < 1.1));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <group>
      {particles.map((particle) => (
        <Particle key={particle.id} data={particle} />
      ))}
    </group>
  );
}

function Particle({ data }: { data: ActiveParticle }) {
  const ref = useRef<THREE.Mesh>(null);
  const progress = useRef(data.progress);

  useFrame((_, delta) => {
    progress.current += delta * 1.5;
    if (ref.current && progress.current < 1) {
      const pos = new THREE.Vector3().lerpVectors(
        data.fromPos,
        data.toPos,
        progress.current
      );
      ref.current.position.copy(pos);
    }
    data.progress = progress.current;
  });

  if (progress.current >= 1) return null;

  return (
    <mesh ref={ref} position={data.fromPos}>
      <sphereGeometry args={[0.04, 8, 8]} />
      <meshBasicMaterial
        color={data.color}
        transparent
        opacity={0.8}
      />
    </mesh>
  );
}
