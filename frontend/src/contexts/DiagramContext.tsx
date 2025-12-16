import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Node, Edge } from '@xyflow/react';

export interface DiagramStructure {
  nodes: Array<{
    id: string;
    type: string;
    label: string;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
  }>;
}

interface DiagramContextType {
  diagramStructure: DiagramStructure;
  updateDiagram: (nodes: Node[], edges: Edge[]) => void;
}

const DiagramContext = createContext<DiagramContextType | undefined>(undefined);

export const DiagramProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [diagramStructure, setDiagramStructure] = useState<DiagramStructure>({
    nodes: [],
    edges: [],
  });

  const updateDiagram = (nodes: Node[], edges: Edge[]) => {
    const serializedNodes = nodes.map(node => ({
      id: node.id,
      type: node.data.nodeType || 'agent', // Use nodeType from data, default to 'agent'
      label: typeof node.data.label === 'string' ? node.data.label : String(node.data.label),
    }));

    const serializedEdges = edges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
    }));

    setDiagramStructure({
      nodes: serializedNodes,
      edges: serializedEdges,
    });
  };

  return (
    <DiagramContext.Provider value={{ diagramStructure, updateDiagram }}>
      {children}
    </DiagramContext.Provider>
  );
};

export const useDiagram = () => {
  const context = useContext(DiagramContext);
  if (context === undefined) {
    throw new Error('useDiagram must be used within a DiagramProvider');
  }
  return context;
};
