import React, { useCallback } from 'react';
import {
  Background,
  ReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import './ArchitectureDiagram.css';

interface ArchitectureDiagramProps {
  isDarkMode: boolean;
}

const initialNodes: Node[] = [
  {
    id: 'agent',
    sourcePosition: Position.Right,
    type: 'input',
    data: { label: '🤖 AI Agent' },
    position: { x: 0, y: 80 },
  },
  {
    id: 'query-human',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    data: { label: '🔧 query_human' },
    position: { x: 300, y: 0 },
  },
  {
    id: 'get-approval',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    data: { label: '🔧 get_approval' },
    position: { x: 300, y: 80 },
  },
  {
    id: 'clarify',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    data: { label: '🔧 clarify' },
    position: { x: 300, y: 160 },
  },
];

const initialEdges = [
  {
    id: 'e1',
    source: 'agent',
    type: 'smoothstep',
    target: 'query-human',
    animated: true,
  },
  {
    id: 'e2',
    source: 'agent',
    type: 'smoothstep',
    target: 'get-approval',
    animated: true,
  },
  {
    id: 'e3',
    source: 'agent',
    type: 'smoothstep',
    target: 'clarify',
    animated: true,
  },
];

const ArchitectureDiagram: React.FC<ArchitectureDiagramProps> = ({ isDarkMode }) => {
  const [nodes, _, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const onConnect = useCallback(
    (params: any) => setEdges((els) => addEdge(params, els)),
    [setEdges],
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      fitView
      attributionPosition="bottom-left"
      className={isDarkMode ? 'dark' : ''}
      style={{ background: isDarkMode ? '#1a1a1a' : '#f7f9fb' }}
    >
      <Background color={isDarkMode ? '#444' : '#ddd'} />
    </ReactFlow>
  );
};

export default ArchitectureDiagram;
