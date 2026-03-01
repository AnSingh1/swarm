"use client";

import { useMemo } from "react";
import { QuadraticBezierLine } from "@react-three/drei";
import { AGENTS } from "../hooks/useAgentData";

function getAgentPosition(index: number): [number, number, number] {
  const totalAgents = 9;
  const arcSpan = Math.PI * 2;
  const angle = (index / totalAgents) * arcSpan;
  const radius = 4.2;
  return [Math.sin(angle) * radius, 0.2, Math.cos(angle) * radius];
}

const CENTER: [number, number, number] = [0, 0, 0];

export function ConnectionLines({ isActive }: { isActive: boolean }) {
  const lines = useMemo(() => {
    return AGENTS.map((agent, i) => {
      const pos = getAgentPosition(i);
      const mid: [number, number, number] = [
        pos[0] * 0.4,
        0.4,
        pos[2] * 0.4,
      ];
      return { agent, start: pos, mid, end: CENTER };
    });
  }, []);

  return (
    <group>
      {lines.map(({ agent, start, mid, end }) => (
        <QuadraticBezierLine
          key={agent.id}
          start={start}
          end={end}
          mid={mid}
          color={agent.color}
          lineWidth={isActive ? 1 : 0.5}
          transparent
          opacity={isActive ? 0.2 : 0.06}
        />
      ))}
    </group>
  );
}
