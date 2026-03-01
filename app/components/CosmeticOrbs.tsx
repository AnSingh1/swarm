"use client";

import { useRef, useState, useEffect } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
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

interface CosmeticOrb {
  id: string;
  fromPos: THREE.Vector3;
  toPos: THREE.Vector3;
  color: string;
  progress: number;
  speed: number;
}

export function CosmeticOrbs({ isActive }: { isActive: boolean }) {
  const [orbs, setOrbs] = useState<CosmeticOrb[]>([]);
  const nextIdRef = useRef(0);
  const pendingTimeoutsRef = useRef<NodeJS.Timeout[]>([]);

  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      // Randomly generate an orb from a random agent
      const fromAgentIdx = Math.floor(Math.random() * 9);
      const fromAgent = AGENTS[fromAgentIdx];
      
      // Use modulo to prevent unbounded counter growth
      const id = `cosmetic_${nextIdRef.current}`;
      nextIdRef.current = (nextIdRef.current + 1) % 100000;
      
      // Phase 1: Agent to center
      setOrbs((prev) => [
        ...prev,
        {
          id: `${id}_to_center`,
          fromPos: getAgentPosition(fromAgentIdx),
          toPos: BLACKBOARD_POS.clone(),
          color: fromAgent.color,
          progress: 0,
          speed: 0.5 + Math.random() * 0.5, // Vary speed a bit
        },
      ]);

      // Phase 2: After reaching center, go to another random agent
      // Track timeout to clean up on unmount
      const timeout = setTimeout(() => {
        let toAgentIdx = Math.floor(Math.random() * 9);
        // Make sure it's different from source
        while (toAgentIdx === fromAgentIdx) {
          toAgentIdx = Math.floor(Math.random() * 9);
        }
        const toAgent = AGENTS[toAgentIdx];
        
        setOrbs((prev) => [
          ...prev,
          {
            id: `${id}_from_center`,
            fromPos: BLACKBOARD_POS.clone(),
            toPos: getAgentPosition(toAgentIdx),
            color: toAgent.color,
            progress: 0,
            speed: 0.5 + Math.random() * 0.5,
          },
        ]);
        
        // Remove this timeout from tracking array after it executes
        pendingTimeoutsRef.current = pendingTimeoutsRef.current.filter(t => t !== timeout);
      }, 600);
      
      pendingTimeoutsRef.current.push(timeout);
    }, 2000 + Math.random() * 3000); // Random interval between 2-5 seconds

    return () => {
      clearInterval(interval);
      // Clear all pending timeouts to prevent memory leak
      pendingTimeoutsRef.current.forEach(timeout => clearTimeout(timeout));
      pendingTimeoutsRef.current = [];
    };
  }, [isActive]);

  useEffect(() => {
    const cleanupInterval = setInterval(() => {
      setOrbs((prev) => prev.filter((orb) => orb.progress < 1.2));
    }, 2000);
    return () => clearInterval(cleanupInterval);
  }, []);

  return (
    <group>
      {orbs.map((orb) => (
        <CosmeticOrb key={orb.id} data={orb} />
      ))}
    </group>
  );
}

function CosmeticOrb({ data }: { data: CosmeticOrb }) {
  const ref = useRef<THREE.Mesh>(null);
  const progress = useRef(data.progress);

  useFrame((_, delta) => {
    progress.current += delta * data.speed;
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
      <sphereGeometry args={[0.03, 8, 8]} />
      <meshBasicMaterial
        color={data.color}
        transparent
        opacity={0.4}
      />
    </mesh>
  );
}
