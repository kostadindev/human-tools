import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, RotateCcw, Activity, Cpu, BarChart2, ArrowRight } from 'lucide-react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Stars, Environment, Box, Icosahedron, Octahedron, Cylinder, Torus } from '@react-three/drei';
import * as THREE from 'three';
import { useNavigate } from 'react-router-dom';
import { Button } from 'antd';

// Nobel gold color constant
const NOBEL_GOLD = '#C5A059';

// --- SURFACE CODE DIAGRAM ---
export const SurfaceCodeDiagram: React.FC = () => {
  const [errors, setErrors] = useState<number[]>([]);

  const adjacency: Record<number, number[]> = {
    0: [0, 1],
    1: [0, 2],
    2: [1, 3],
    3: [2, 3],
    4: [0, 1, 2, 3],
  };

  const toggleError = (id: number) => {
    setErrors(prev => prev.includes(id) ? prev.filter(e => e !== id) : [...prev, id]);
  };

  const activeStabilizers = [0, 1, 2, 3].filter(stabId => {
    let errorCount = 0;
    Object.entries(adjacency).forEach(([dataId, stabs]) => {
      if (errors.includes(parseInt(dataId)) && stabs.includes(stabId)) {
        errorCount++;
      }
    });
    return errorCount % 2 !== 0;
  });

  return (
    <div className="flex flex-col items-center p-8 bg-white rounded-xl shadow-sm border border-stone-200 my-8">
      <h3 className="font-serif text-xl mb-4 text-stone-800">Interactive: Surface Code Detection</h3>
      <p className="text-sm text-stone-500 mb-6 text-center max-w-md">
        Click the grey <strong>Data Qubits</strong> to inject errors. Watch the colored <strong>Stabilizers</strong> light up when they detect an odd number of errors.
      </p>
      
      <div className="relative w-64 h-64 bg-[#F5F4F0] rounded-lg border border-stone-200 p-4 flex flex-wrap justify-between content-between">
        {/* Grid Lines */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-20">
          <div className="w-2/3 h-2/3 border border-stone-400"></div>
          <div className="absolute w-full h-[1px] bg-stone-400"></div>
          <div className="absolute h-full w-[1px] bg-stone-400"></div>
        </div>
        
        {/* Stabilizers */}
        {[
          {id: 0, x: '50%', y: '20%', type: 'Z', color: 'bg-blue-500'},
          {id: 1, x: '20%', y: '50%', type: 'X', color: 'bg-red-500'},
          {id: 2, x: '80%', y: '50%', type: 'X', color: 'bg-red-500'},
          {id: 3, x: '50%', y: '80%', type: 'Z', color: 'bg-blue-500'},
        ].map(stab => (
          <motion.div
            key={`stab-${stab.id}`}
            className={`absolute w-10 h-10 -ml-5 -mt-5 flex items-center justify-center text-white text-xs font-bold rounded-sm shadow-sm transition-all duration-300 ${activeStabilizers.includes(stab.id) ? stab.color + ' opacity-100 scale-110 ring-4 ring-offset-2 ring-stone-200' : 'bg-stone-300 opacity-40'}`}
            style={{ left: stab.x, top: stab.y }}
          >
            {stab.type}
          </motion.div>
        ))}
        
        {/* Data Qubits */}
        {[
          {id: 0, x: '20%', y: '20%'}, {id: 1, x: '80%', y: '20%'},
          {id: 4, x: '50%', y: '50%'},
          {id: 2, x: '20%', y: '80%'}, {id: 3, x: '80%', y: '80%'},
        ].map(q => (
          <button
            key={`data-${q.id}`}
            onClick={() => toggleError(q.id)}
            className={`absolute w-8 h-8 -ml-4 -mt-4 rounded-full border-2 flex items-center justify-center transition-all duration-200 z-10 ${errors.includes(q.id) ? 'bg-stone-800 border-stone-900' : 'bg-white border-stone-300 hover:border-stone-500'}`}
            style={{ left: q.x, top: q.y, color: errors.includes(q.id) ? NOBEL_GOLD : undefined }}
          >
            {errors.includes(q.id) && <Activity size={14} />}
          </button>
        ))}
      </div>
      
      <div className="mt-6 flex items-center gap-4 text-xs font-mono text-stone-500">
        <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-stone-800"></div> Error</div>
        <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-blue-500"></div> Z-Check</div>
        <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-red-500"></div> X-Check</div>
      </div>
      
      <div className="mt-4 h-6 text-sm font-serif italic text-stone-600">
        {errors.length === 0 ? "System is stable." : `Detected ${activeStabilizers.length} parity violations.`}
      </div>
    </div>
  );
};

// --- TRANSFORMER DECODER DIAGRAM ---
export const TransformerDecoderDiagram: React.FC = () => {
  const [step, setStep] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setStep(s => (s + 1) % 4);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center p-8 bg-[#F5F4F0] rounded-xl border border-stone-200 my-8">
      <h3 className="font-serif text-xl mb-4 text-stone-900">AlphaQubit Architecture</h3>
      <p className="text-sm text-stone-600 mb-6 text-center max-w-md">
        The model processes syndrome history using a recurrent transformer, attending to spatial and temporal correlations.
      </p>
      <div className="relative w-full max-w-lg h-56 bg-white rounded-lg shadow-inner overflow-hidden mb-6 border border-stone-200 flex items-center justify-center gap-8 p-4">
        {/* Input Stage */}
        <div className="flex flex-col items-center gap-2">
          <div className={`w-16 h-16 rounded-lg border-2 flex flex-col items-center justify-center transition-colors duration-500 ${step === 0 ? 'border-[#C5A059] bg-[#C5A059]/10' : 'border-stone-200 bg-stone-50'}`}>
            <div className="grid grid-cols-3 gap-1">
              {[...Array(9)].map((_, i) => <div key={i} className={`w-2 h-2 rounded-full ${Math.random() > 0.7 ? 'bg-stone-800' : 'bg-stone-300'}`}></div>)}
            </div>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider text-stone-500">Syndrome</span>
        </div>
        
        <motion.div animate={{ opacity: step >= 1 ? 1 : 0.3, x: step >= 1 ? 0 : -5 }}>→</motion.div>
        
        {/* Transformer Stage */}
        <div className="flex flex-col items-center gap-2">
          <div className={`w-24 h-24 rounded-xl border-2 flex flex-col items-center justify-center gap-2 transition-colors duration-500 relative overflow-hidden ${step === 1 || step === 2 ? 'border-stone-800 bg-stone-900 text-white' : 'border-stone-200 bg-stone-50'}`}>
            <Cpu size={24} className={step === 1 || step === 2 ? 'text-[#C5A059] animate-pulse' : 'text-stone-300'} />
            {step === 1 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-full h-[1px] bg-[#C5A059] absolute top-1/3 animate-ping"></div>
                <div className="w-full h-[1px] bg-[#C5A059] absolute top-2/3 animate-ping"></div>
              </div>
            )}
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider text-stone-500">Transformer</span>
        </div>
        
        <motion.div animate={{ opacity: step >= 3 ? 1 : 0.3, x: step >= 3 ? 0 : -5 }}>→</motion.div>
        
        {/* Output Stage */}
        <div className="flex flex-col items-center gap-2">
          <div className={`w-16 h-16 rounded-lg border-2 flex flex-col items-center justify-center transition-colors duration-500 ${step === 3 ? 'border-green-500 bg-green-50' : 'border-stone-200 bg-stone-50'}`}>
            {step === 3 ? (
              <span className="text-2xl font-serif text-green-600">X</span>
            ) : (
              <span className="text-2xl font-serif text-stone-300">?</span>
            )}
          </div>
          <span className="text-[10px] uppercase font-bold tracking-wider text-stone-500">Correction</span>
        </div>
      </div>
      <div className="flex gap-2">
        {[0, 1, 2, 3].map(s => (
          <div key={s} className={`h-1 rounded-full transition-all duration-300 ${step === s ? 'w-8 bg-[#C5A059]' : 'w-2 bg-stone-300'}`}></div>
        ))}
      </div>
    </div>
  );
};

// --- PERFORMANCE CHART ---
export const PerformanceMetricDiagram: React.FC = () => {
  const [distance, setDistance] = useState<3 | 5 | 11>(5);
  
  const data = {
    3: { mwpm: 3.5, alpha: 2.9 },
    5: { mwpm: 3.6, alpha: 2.75 },
    11: { mwpm: 0.0041, alpha: 0.0009 }
  };

  const currentData = data[distance];
  const maxVal = Math.max(currentData.mwpm, currentData.alpha) * 1.25;
  
  const formatValue = (val: number) => {
    if (val < 0.01) return val.toFixed(4) + '%';
    return val.toFixed(2) + '%';
  };

  return (
    <div className="flex flex-col md:flex-row gap-8 items-center p-8 bg-stone-900 text-stone-100 rounded-xl my-8 border border-stone-800 shadow-lg">
      <div className="flex-1 min-w-[240px]">
        <h3 className="font-serif text-xl mb-2 text-[#C5A059]">Performance vs Standard</h3>
        <p className="text-stone-400 text-sm mb-4 leading-relaxed">
          AlphaQubit consistently achieves lower logical error rates (LER) than the standard Minimum-Weight Perfect Matching (MWPM) decoder.
        </p>
        <div className="flex gap-2 mt-6">
          {[3, 5, 11].map((d) => (
            <button
              key={d}
              onClick={() => setDistance(d as any)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-all duration-200 border ${distance === d ? 'bg-[#C5A059] text-stone-900 border-[#C5A059]' : 'bg-transparent text-stone-400 border-stone-700 hover:border-stone-500 hover:text-stone-200'}`}
            >
              Distance {d}
            </button>
          ))}
        </div>
        <div className="mt-6 font-mono text-xs text-stone-500 flex items-center gap-2">
          <BarChart2 size={14} className="text-[#C5A059]" />
          <span>LOGICAL ERROR RATE (LOWER IS BETTER)</span>
        </div>
      </div>
      
      <div className="relative w-64 h-72 bg-stone-800/50 rounded-xl border border-stone-700/50 p-6 flex justify-around items-end">
        <div className="absolute inset-0 p-6 flex flex-col justify-between pointer-events-none opacity-10">
          <div className="w-full h-[1px] bg-stone-400"></div>
          <div className="w-full h-[1px] bg-stone-400"></div>
          <div className="w-full h-[1px] bg-stone-400"></div>
          <div className="w-full h-[1px] bg-stone-400"></div>
        </div>
        
        {/* MWPM Bar */}
        <div className="w-20 flex flex-col justify-end items-center h-full z-10">
          <div className="flex-1 w-full flex items-end justify-center relative mb-3">
            <div className="absolute -top-5 w-full text-center text-sm font-mono text-stone-400 font-bold bg-stone-900/90 py-1 px-2 rounded backdrop-blur-sm border border-stone-700/50 shadow-sm">{formatValue(currentData.mwpm)}</div>
            <motion.div
              className="w-full bg-stone-600 rounded-t-md border-t border-x border-stone-500/30"
              initial={{ height: 0 }}
              animate={{ height: `${(currentData.mwpm / maxVal) * 100}%` }}
              transition={{ type: "spring", stiffness: 80, damping: 15 }}
            />
          </div>
          <div className="h-6 flex items-center text-xs font-bold text-stone-500 uppercase tracking-wider">Standard</div>
        </div>
        
        {/* AlphaQubit Bar */}
        <div className="w-20 flex flex-col justify-end items-center h-full z-10">
          <div className="flex-1 w-full flex items-end justify-center relative mb-3">
            <div className="absolute -top-5 w-full text-center text-sm font-mono text-[#C5A059] font-bold bg-stone-900/90 py-1 px-2 rounded backdrop-blur-sm border border-[#C5A059]/30 shadow-sm">{formatValue(currentData.alpha)}</div>
            <motion.div
              className="w-full bg-[#C5A059] rounded-t-md shadow-[0_0_20px_rgba(197,160,89,0.25)] relative overflow-hidden"
              initial={{ height: 0 }}
              animate={{ height: Math.max(1, (currentData.alpha / maxVal) * 100) + '%' }}
              transition={{ type: "spring", stiffness: 80, damping: 15, delay: 0.1 }}
            >
              <div className="absolute inset-0 bg-gradient-to-tr from-transparent to-white/20"></div>
            </motion.div>
          </div>
          <div className="h-6 flex items-center text-xs font-bold text-[#C5A059] uppercase tracking-wider">AlphaQubit</div>
        </div>
      </div>
    </div>
  );
};

// --- 3D SCENES ---
const LatticeNode = ({ position, color, delay }: { position: [number, number, number]; color: string; delay: number }) => {
  const ref = useRef<THREE.Mesh>(null);
  
  useFrame((state) => {
    if (ref.current) {
      const t = state.clock.getElapsedTime();
      const wave = Math.sin(t * 1.5 + delay) * 0.15;
      ref.current.position.y = position[1] + wave;
      const pulse = 1 + Math.sin(t * 2 + delay) * 0.1;
      ref.current.scale.set(pulse, pulse, pulse);
      ref.current.rotation.x = t * 0.2;
      ref.current.rotation.y = t * 0.3;
    }
  });

  return (
    <Octahedron ref={ref} args={[0.2, 0]} position={position}>
      <meshPhysicalMaterial
        color={color}
        metalness={0.9}
        roughness={0.1}
        emissive={color}
        emissiveIntensity={0.2}
        transparent
        opacity={0.8}
      />
    </Octahedron>
  );
};

const NeuralCore = () => {
  const ref = useRef<THREE.Group>(null);
  const crystalRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.getElapsedTime() * 0.1;
    }
    if (crystalRef.current) {
      crystalRef.current.rotation.x = state.clock.getElapsedTime() * 0.5;
      crystalRef.current.rotation.z = state.clock.getElapsedTime() * 0.3;
    }
  });

  return (
    <group ref={ref}>
      <Icosahedron args={[1.5, 1]}>
        <meshStandardMaterial color={NOBEL_GOLD} wireframe transparent opacity={0.15} />
      </Icosahedron>
      
      <Icosahedron ref={crystalRef} args={[0.8, 0]}>
        <meshPhysicalMaterial
          color={NOBEL_GOLD}
          metalness={1}
          roughness={0}
          transmission={0.5}
          thickness={1}
          emissive={NOBEL_GOLD}
          emissiveIntensity={0.5}
        />
      </Icosahedron>
      
      <pointLight color={NOBEL_GOLD} intensity={2} distance={5} />
    </group>
  );
};

const NeuralLatticeField = () => {
  const nodes = useMemo(() => {
    const temp = [];
    const size = 5;
    const spacing = 1.8;
    for (let x = -size; x <= size; x++) {
      for (let z = -size; z <= size; z++) {
        const dist = Math.sqrt(x * x + z * z);
        if (dist > 1.5 && dist < 5.5) {
          temp.push({
            pos: [x * spacing, -1.5, z * spacing] as [number, number, number],
            delay: dist * 0.5,
            color: Math.random() > 0.8 ? NOBEL_GOLD : "#4F46E5"
          });
        }
      }
    }
    return temp;
  }, []);

  return (
    <group>
      {nodes.map((node, i) => (
        <LatticeNode key={i} position={node.pos} color={node.color} delay={node.delay} />
      ))}
    </group>
  );
};

export const HeroScene: React.FC = () => {
  return (
    <div className="absolute inset-0 z-0 opacity-80 pointer-events-none">
      <Canvas camera={{ position: [0, 4, 10], fov: 40 }}>
        <fog attach="fog" args={['#F9F8F4', 5, 20]} />
        <ambientLight intensity={0.4} />
        <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={2} />
        <pointLight position={[-10, -10, -10]} color="#4F46E5" intensity={1} />
        
        <Float speed={1.2} rotationIntensity={0.3} floatIntensity={0.4}>
          <NeuralCore />
          <NeuralLatticeField />
        </Float>

        <Environment preset="city" />
        <Stars radius={50} depth={50} count={2000} factor={4} saturation={0} fade speed={0.5} />
      </Canvas>
    </div>
  );
};

export const QuantumComputerScene: React.FC = () => {
  return (
    <div className="w-full h-full absolute inset-0">
      <Canvas camera={{ position: [0, 0, 4.5], fov: 45 }}>
        <ambientLight intensity={1} />
        <spotLight position={[5, 5, 5]} angle={0.3} penumbra={1} intensity={2} color={NOBEL_GOLD} />
        <pointLight position={[-5, -5, -5]} intensity={0.5} />
        <Environment preset="studio" />
        
        <Float rotationIntensity={0.4} floatIntensity={0.2} speed={1}>
          <group rotation={[0, 0, 0]} position={[0, 0.5, 0]}>
            <Cylinder args={[1.2, 1.2, 0.1, 64]} position={[0, 1, 0]}>
              <meshStandardMaterial color={NOBEL_GOLD} metalness={1} roughness={0.15} />
            </Cylinder>
            
            <Cylinder args={[1, 1, 0.1, 64]} position={[0, 0.2, 0]}>
              <meshStandardMaterial color={NOBEL_GOLD} metalness={1} roughness={0.15} />
            </Cylinder>
            
            <Cylinder args={[0.6, 0.6, 0.1, 64]} position={[0, -0.6, 0]}>
              <meshStandardMaterial color={NOBEL_GOLD} metalness={1} roughness={0.15} />
            </Cylinder>

            <Cylinder args={[0.04, 0.04, 0.8, 16]} position={[0.5, 0.6, 0]}>
              <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>
            <Cylinder args={[0.04, 0.04, 0.8, 16]} position={[-0.5, 0.6, 0]}>
              <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>
            <Cylinder args={[0.04, 0.04, 0.8, 16]} position={[0, 0.6, 0.5]}>
              <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>
            <Cylinder args={[0.04, 0.04, 0.8, 16]} position={[0, 0.6, -0.5]}>
              <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>

            <Cylinder args={[0.03, 0.03, 0.8, 16]} position={[0.2, -0.2, 0]}>
              <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>
            <Cylinder args={[0.03, 0.03, 0.8, 16]} position={[-0.2, -0.2, 0]}>
              <meshStandardMaterial color="#D1D5DB" metalness={0.8} roughness={0.2} />
            </Cylinder>

            <Torus args={[0.7, 0.015, 16, 64]} position={[0, -0.2, 0]} rotation={[Math.PI/2, 0, 0]}>
              <meshStandardMaterial color="#B87333" metalness={0.8} roughness={0.3} />
            </Torus>
            <Torus args={[0.3, 0.015, 16, 64]} position={[0, -1, 0]} rotation={[Math.PI/2, 0, 0]}>
              <meshStandardMaterial color="#B87333" metalness={0.8} roughness={0.3} />
            </Torus>
            
            <Box args={[0.2, 0.05, 0.2]} position={[0, -0.7, 0]}>
              <meshStandardMaterial color="#111" metalness={0.9} roughness={0.1} />
            </Box>
          </group>
        </Float>
      </Canvas>
    </div>
  );
};

// --- MAIN LANDING PAGE ---
const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F9F8F4] relative overflow-x-hidden">
      <HeroScene />
      
      {/* Header */}
      <header className="relative z-10 px-8 py-6 flex justify-between items-center">
        <div className="text-2xl font-serif font-bold text-stone-800">Human Tools</div>
        <Button
          type="primary"
          size="large"
          onClick={() => navigate('/chat')}
          className="bg-[#C5A059] hover:bg-[#B8954F] border-none"
          icon={<ArrowRight size={16} />}
        >
          Get Started
        </Button>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 px-8 py-20 text-center">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-6xl md:text-7xl font-serif font-bold text-stone-900 mb-6"
        >
          Multi-Agent
          <br />
          <span className="text-[#C5A059]">Collaboration</span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="text-xl text-stone-600 max-w-2xl mx-auto mb-12"
        >
          Orchestrate specialized AI agents and human collaborators to solve complex problems together.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          <Button
            type="primary"
            size="large"
            onClick={() => navigate('/chat')}
            className="bg-[#C5A059] hover:bg-[#B8954F] border-none h-12 px-8 text-lg"
            icon={<Play size={20} />}
          >
            Start Collaborating
          </Button>
        </motion.div>
      </section>

      {/* Diagrams Section */}
      <section className="relative z-10 px-8 py-20 max-w-6xl mx-auto">
        <SurfaceCodeDiagram />
        <TransformerDecoderDiagram />
        <PerformanceMetricDiagram />
      </section>

      {/* Features Section */}
      <section className="relative z-10 px-8 py-20 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-serif font-bold text-center text-stone-900 mb-16">Key Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { title: 'Agent Orchestration', desc: 'Coordinate multiple specialized AI agents seamlessly' },
              { title: 'Human-in-the-Loop', desc: 'Integrate human judgment and expertise when needed' },
              { title: 'Real-time Collaboration', desc: 'Work together with agents and humans in real-time' },
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
                className="p-6 rounded-xl bg-stone-50 border border-stone-200"
              >
                <h3 className="text-xl font-serif font-bold text-stone-900 mb-3">{feature.title}</h3>
                <p className="text-stone-600">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 px-8 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
          className="max-w-2xl mx-auto"
        >
          <h2 className="text-4xl font-serif font-bold text-stone-900 mb-6">Ready to Get Started?</h2>
          <p className="text-xl text-stone-600 mb-8">
            Experience the power of multi-agent collaboration with human expertise.
          </p>
          <Button
            type="primary"
            size="large"
            onClick={() => navigate('/chat')}
            className="bg-[#C5A059] hover:bg-[#B8954F] border-none h-12 px-8 text-lg"
            icon={<ArrowRight size={20} />}
          >
            Launch Application
          </Button>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 px-8 py-8 text-center text-stone-500 text-sm border-t border-stone-200">
        <p>© 2024 Human Tools. Built for collaborative AI systems.</p>
      </footer>
    </div>
  );
};

export default LandingPage;

