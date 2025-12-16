import React, { useCallback, useState } from 'react';
import {
  Background,
  ReactFlow,
  useNodesState,
  useEdgesState,
  addEdge,
  Node,
  Position,
  Controls,
  MiniMap,
} from '@xyflow/react';
import { Button } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import '@xyflow/react/dist/style.css';
import './ArchitectureDiagram.css';

interface ArchitectureDiagramProps {
  isDarkMode: boolean;
}

const initialNodes: Node[] = [
  {
    id: 'orchestrator',
    sourcePosition: Position.Right,
    type: 'input',
    data: { label: '🎯 Orchestrator' },
    position: { x: 0, y: 80 },
  },
  {
    id: 'agent-1',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    type: 'default',
    data: { label: '🤖 Agent 1' },
    position: { x: 300, y: 0 },
  },
  {
    id: 'agent-2',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    type: 'default',
    data: { label: '🤖 Agent 2' },
    position: { x: 300, y: 80 },
  },
  {
    id: 'agent-3',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    type: 'default',
    data: { label: '🤖 Agent 3' },
    position: { x: 300, y: 160 },
  },
];

const initialEdges = [
  {
    id: 'e1',
    source: 'orchestrator',
    type: 'smoothstep',
    target: 'agent-1',
    animated: true,
  },
  {
    id: 'e2',
    source: 'orchestrator',
    type: 'smoothstep',
    target: 'agent-2',
    animated: true,
  },
  {
    id: 'e3',
    source: 'orchestrator',
    type: 'smoothstep',
    target: 'agent-3',
    animated: true,
  },
];

let nodeId = 4;

const ArchitectureDiagram: React.FC<ArchitectureDiagramProps> = ({ isDarkMode }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(
    (params: any) => setEdges((els) => addEdge({ ...params, type: 'smoothstep', animated: true }, els)),
    [setEdges],
  );

  const addAgentNode = useCallback(() => {
    const newNode: Node = {
      id: `agent-${nodeId++}`,
      sourcePosition: Position.Right,
      type: 'input',
      data: { label: '🤖 Agent' },
      position: { x: Math.random() * 400, y: Math.random() * 300 },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [setNodes]);

  const addToolNode = useCallback(() => {
    const newNode: Node = {
      id: `tool-${nodeId++}`,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      data: { label: '🔧 tool' },
      position: { x: Math.random() * 400 + 300, y: Math.random() * 300 },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [setNodes]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div style={{
        position: 'absolute',
        top: 10,
        right: 10,
        zIndex: 10,
        display: 'flex',
        gap: '8px'
      }}>
        <Button
          icon={<PlusOutlined />}
          onClick={addAgentNode}
          type="primary"
        >
          Add Agent
        </Button>
        <Button
          icon={<PlusOutlined />}
          onClick={addToolNode}
        >
          Add Tool
        </Button>
      </div>

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
        <Controls />
        <MiniMap
          style={{
            background: isDarkMode ? '#2a2a2a' : '#f7f9fb',
          }}
        />
      </ReactFlow>
    </div>
  );
};

export default ArchitectureDiagram;
