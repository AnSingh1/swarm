"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

export function BlackboardSphere({ isActive }: { isActive: boolean }) {
  const sphereRef = useRef<THREE.Mesh>(null);
  const glowRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (sphereRef.current) {
      sphereRef.current.rotation.y = t * 0.3;
      sphereRef.current.rotation.x = Math.sin(t * 0.2) * 0.1;
    }
    if (glowRef.current) {
      const pulse = isActive ? 0.3 + Math.sin(t * 1.5) * 0.15 : 0.08;
      (glowRef.current.material as THREE.MeshBasicMaterial).opacity = pulse;
      const s = 1 + Math.sin(t * 1.5) * 0.05;
      glowRef.current.scale.set(s, s, s);
    }
    if (ringRef.current) {
      ringRef.current.rotation.z = t * 0.5;
      ringRef.current.rotation.x = Math.PI / 2 + Math.sin(t * 0.3) * 0.2;
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Outer glow */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[0.55, 32, 32]} />
        <meshBasicMaterial
          color="#00f0ff"
          transparent
          opacity={0.15}
          side={THREE.BackSide}
        />
      </mesh>

      {/* Core sphere */}
      <mesh ref={sphereRef}>
        <icosahedronGeometry args={[0.3, 2]} />
        <meshStandardMaterial
          color="#0a0f14"
          emissive="#00f0ff"
          emissiveIntensity={isActive ? 0.6 : 0.15}
          wireframe
          transparent
          opacity={0.9}
        />
      </mesh>

      {/* Inner solid core */}
      <mesh>
        <sphereGeometry args={[0.15, 16, 16]} />
        <meshStandardMaterial
          color="#00f0ff"
          emissive="#00f0ff"
          emissiveIntensity={isActive ? 1.2 : 0.3}
          transparent
          opacity={0.6}
        />
      </mesh>

      {/* Orbital ring */}
      <mesh ref={ringRef} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.45, 0.008, 8, 64]} />
        <meshBasicMaterial
          color="#00f0ff"
          transparent
          opacity={isActive ? 0.5 : 0.15}
        />
      </mesh>

      {/* Point light for scene illumination */}
      <pointLight
        color="#00f0ff"
        intensity={isActive ? 2 : 0.3}
        distance={8}
        decay={2}
      />
    </group>
  );
}
