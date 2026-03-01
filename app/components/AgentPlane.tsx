"use client";

import { useRef, useMemo } from "react";
import { useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import * as THREE from "three";

interface AgentPlaneProps {
  position: [number, number, number];
  rotation: [number, number, number];
  agentName: string;
  agentColor: string;
  agentRole: string;
  agentId: number;
  status: string;
  liveUrl: string | null;
  isActive: boolean;
}

export function AgentPlane({
  position,
  rotation,
  agentName,
  agentColor,
  agentRole,
  agentId,
  status,
  liveUrl,
  isActive,
}: AgentPlaneProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    const t = state.clock.elapsedTime;
    meshRef.current.position.y =
      position[1] + Math.sin(t * 0.5 + position[0]) * 0.04;

    if (glowRef.current) {
      const scale = isActive ? 1.02 + Math.sin(t * 2) * 0.008 : 1.02;
      glowRef.current.scale.set(scale, scale, 1);
    }
  });

  const borderColor = useMemo(
    () => new THREE.Color(agentColor),
    [agentColor]
  );

  return (
    <group position={position} rotation={rotation}>
      {/* Glow border */}
      <mesh ref={glowRef} position={[0, 0, -0.01]}>
        <planeGeometry args={[2.08, 1.33]} />
        <meshBasicMaterial
          color={borderColor}
          transparent
          opacity={isActive ? 0.35 : 0.1}
        />
      </mesh>

      {/* Screen plane background */}
      <mesh ref={meshRef}>
        <planeGeometry args={[2, 1.25]} />
        <meshStandardMaterial
          color="#0a0b0f"
          emissive={agentColor}
          emissiveIntensity={0.05}
          roughness={0.3}
          metalness={0.1}
        />
      </mesh>

      {/* Live stream iframe overlay */}
      <Html
        transform
        position={[0, 0, 0.01]}
        scale={0.3}
        distanceFactor={3}
        style={{ pointerEvents: "none" }}
      >
        <div
          style={{
            width: 640,
            height: 400,
            background: "#0a0b0f",
            borderRadius: 4,
            overflow: "hidden",
            position: "relative",
          }}
        >
          {liveUrl ? (
            <iframe
              src={liveUrl}
              style={{
                width: "100%",
                height: "100%",
                border: "none",
                pointerEvents: "none",
              }}
              title={`Agent ${agentId} Stream`}
              allow="autoplay"
            />
          ) : (
            <div
              style={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                color: agentColor,
                fontFamily: "'JetBrains Mono', monospace",
                gap: 8,
              }}
            >
              <div
                style={{
                  width: 32,
                  height: 32,
                  border: `2px solid ${agentColor}40`,
                  borderTopColor: agentColor,
                  borderRadius: "50%",
                  animation: "spin 1s linear infinite",
                }}
              />
              <span style={{ fontSize: 10, opacity: 0.7 }}>
                Waiting for stream...
              </span>
            </div>
          )}
        </div>
      </Html>

      {/* Scanline overlay */}
      {isActive && (
        <mesh position={[0, 0, 0.005]}>
          <planeGeometry args={[2, 1.25]} />
          <meshBasicMaterial color={agentColor} transparent opacity={0.03} />
        </mesh>
      )}

      {/* Label */}
      <Html
        position={[0, -0.78, 0]}
        center
        distanceFactor={6}
        style={{ pointerEvents: "none" }}
      >
        <div
          style={{
            fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
            textAlign: "center",
            whiteSpace: "nowrap",
          }}
        >
          <div
            style={{
              fontSize: 10,
              color: agentColor,
              textTransform: "uppercase",
              letterSpacing: 2,
              textShadow: `0 0 8px ${agentColor}40`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 6,
            }}
          >
            <span style={{ fontWeight: 700 }}>{agentName}</span>
            {isActive && (
              <span
                style={{
                  display: "inline-block",
                  width: 5,
                  height: 5,
                  borderRadius: "50%",
                  backgroundColor: agentColor,
                  boxShadow: `0 0 6px ${agentColor}`,
                  animation: "pulse 1.5s infinite",
                }}
              />
            )}
          </div>

          {isActive && (
            <div
              style={{
                marginTop: 3,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
              }}
            >
              <span
                style={{
                  fontSize: 7,
                  color: `${agentColor}90`,
                  letterSpacing: 1.5,
                  textTransform: "uppercase",
                  fontWeight: 500,
                }}
              >
                {status}
              </span>
              <div
                style={{
                  width: 32,
                  height: 2,
                  background: `${agentColor}15`,
                  borderRadius: 1,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: "60%",
                    height: "100%",
                    background: agentColor,
                    borderRadius: 1,
                    animation: "pulse 2s infinite",
                  }}
                />
              </div>
            </div>
          )}
        </div>
        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
          }
        `}</style>
      </Html>
    </group>
  );
}
