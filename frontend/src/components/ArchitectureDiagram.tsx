import React, { useCallback, useState, useEffect } from 'react';
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
  NodeMouseHandler,
} from '@xyflow/react';
import { Button, Modal, Card, Typography, Timeline, Tag } from 'antd';
import '@xyflow/react/dist/style.css';
import './ArchitectureDiagram.css';
import { useDiagram } from '../contexts/DiagramContext';

const { Title, Paragraph, Text } = Typography;

interface ArchitectureDiagramProps {
  isDarkMode: boolean;
}

const initialNodes: Node[] = [
  {
    id: 'orchestrator',
    sourcePosition: Position.Right,
    type: 'input',
    data: { label: '🎯 Orchestrator', nodeType: 'orchestrator' },
    position: { x: 0, y: 80 },
  },
  {
    id: 'agent-1',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    type: 'default',
    data: { label: '🔬 Analytical', nodeType: 'agent' },
    position: { x: 300, y: 0 },
  },
  {
    id: 'agent-2',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    type: 'default',
    data: { label: '🎨 Creative', nodeType: 'agent' },
    position: { x: 300, y: 80 },
  },
  {
    id: 'human',
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
    type: 'default',
    data: { label: '👤 Human', nodeType: 'human' },
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
    target: 'human',
    animated: true,
  },
];

let nodeId = 4;

const DIAGRAM_STORAGE_KEY = 'diagram_state';

// Mock agent data
interface AgentHistory {
  id: string;
  timestamp: string;
  action: string;
  status: 'success' | 'error' | 'pending';
}

interface AgentData {
  id: string;
  name: string;
  description: string;
  type: string;
  capabilities: string[];
  history: AgentHistory[];
}

// Agent metadata (static information about each agent/human)
const agentMetadata: Record<string, Omit<AgentData, 'id' | 'history'>> = {
  'agent-1': {
    name: 'Analytical Agent',
    description: 'A specialized agent designed for data analysis, pattern recognition, and logical reasoning. This agent excels at breaking down complex problems into manageable components and providing data-driven insights.',
    type: 'Analytical',
    capabilities: ['Data Analysis', 'Pattern Recognition', 'Statistical Modeling', 'Report Generation'],
  },
  'agent-2': {
    name: 'Creative Agent',
    description: 'An innovative agent focused on creative problem-solving, content generation, and artistic expression. This agent brings creativity and out-of-the-box thinking to complex challenges.',
    type: 'Creative',
    capabilities: ['Content Generation', 'Creative Writing', 'Design Concepts', 'Brainstorming'],
  },
  'human': {
    name: 'Human Collaborator',
    description: 'A human collaborator who provides judgment, preferences, approval, and information that requires human insight. The human collaborator works asynchronously with the AI agents to provide critical input.',
    type: 'Human',
    capabilities: ['Decision Making', 'Judgment', 'Approval', 'Contextual Knowledge'],
  },
};

// Fetch agent history from backend
const fetchAgentHistory = async (agentId: string): Promise<AgentHistory[]> => {
  try {
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
    const response = await fetch(`${API_URL}/agent/${agentId}/history`);
    if (!response.ok) {
      return [];
    }
    const data = await response.json();
    return data.history || [];
  } catch (error) {
    console.error(`Error fetching history for ${agentId}:`, error);
    return [];
  }
};

// Load saved diagram from localStorage or use initial values
const loadSavedDiagram = () => {
  try {
    const saved = localStorage.getItem(DIAGRAM_STORAGE_KEY);
    if (saved) {
      const { nodes, edges } = JSON.parse(saved);
      // Update nodeId to be higher than any existing node
      const maxId = nodes.reduce((max: number, node: Node) => {
        const match = node.id.match(/\d+$/);
        if (match) {
          const id = parseInt(match[0], 10);
          return Math.max(max, id);
        }
        return max;
      }, 0);
      nodeId = maxId + 1;
      return { nodes, edges };
    }
  } catch (error) {
    console.error('Error loading saved diagram:', error);
  }
  return { nodes: initialNodes, edges: initialEdges };
};

const ArchitectureDiagram: React.FC<ArchitectureDiagramProps> = ({ isDarkMode }) => {
  const savedDiagram = loadSavedDiagram();
  const [nodes, setNodes, onNodesChange] = useNodesState(savedDiagram.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(savedDiagram.edges);
  const { updateDiagram } = useDiagram();
  const [selectedAgent, setSelectedAgent] = useState<AgentData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Update diagram context whenever nodes or edges change
  useEffect(() => {
    updateDiagram(nodes, edges);
  }, [nodes, edges, updateDiagram]);

  // Save diagram to localStorage whenever nodes or edges change
  useEffect(() => {
    try {
      localStorage.setItem(DIAGRAM_STORAGE_KEY, JSON.stringify({ nodes, edges }));
    } catch (error) {
      console.error('Error saving diagram to localStorage:', error);
    }
  }, [nodes, edges]);

  const onConnect = useCallback(
    (params: any) => setEdges((els) => addEdge({ ...params, type: 'smoothstep', animated: true }, els)),
    [setEdges],
  );

  const addAgentNode = useCallback(() => {
    const newNode: Node = {
      id: `agent-${nodeId++}`,
      sourcePosition: Position.Right,
      type: 'input',
      data: { label: '🤖 Agent', nodeType: 'agent' },
      position: { x: Math.random() * 400, y: Math.random() * 300 },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [setNodes]);

  const addToolNode = useCallback(() => {
    const newNode: Node = {
      id: `tool-${nodeId++}`,
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      data: { label: '🔧 tool', nodeType: 'tool' },
      position: { x: Math.random() * 400 + 300, y: Math.random() * 300 },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [setNodes]);

  const resetDiagram = useCallback(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    nodeId = 4;
    localStorage.removeItem(DIAGRAM_STORAGE_KEY);
  }, [setNodes, setEdges]);

  const onNodeClick: NodeMouseHandler = useCallback(async (_event, node) => {
    // Show agent card for agent and human nodes
    if (node.data?.nodeType === 'agent' || node.data?.nodeType === 'human') {
      setIsModalOpen(true);
      
      // Get metadata for this agent/human
      const metadata = agentMetadata[node.id];
      const defaultMetadata = {
        name: (typeof node.data?.label === 'string' ? node.data.label : 'Agent') || 'Agent',
        description: 'A general-purpose agent capable of handling various tasks and coordinating with other agents in the system.',
        type: node.data?.nodeType === 'human' ? 'Human' : 'General',
        capabilities: node.data?.nodeType === 'human' 
          ? ['Decision Making', 'Judgment', 'Approval']
          : ['Task Execution', 'Coordination', 'Communication'],
      };
      
      const agentInfo = metadata || defaultMetadata;
      
      // Fetch history from backend
      const history = await fetchAgentHistory(node.id);
      
      // Format timestamps for display
      const formattedHistory: AgentHistory[] = history.map((item) => {
        let formattedTimestamp = new Date().toLocaleString();
        if (item.timestamp) {
          try {
            const date = new Date(item.timestamp);
            if (!isNaN(date.getTime())) {
              formattedTimestamp = date.toLocaleString('en-US', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              });
            }
          } catch (e) {
            console.warn('Error parsing timestamp:', item.timestamp);
          }
        }
        return {
          ...item,
          timestamp: formattedTimestamp,
          status: (item.status || 'pending') as 'success' | 'error' | 'pending',
        };
      });
      
      const agentData: AgentData = {
        id: node.id,
        ...agentInfo,
        history: formattedHistory.length > 0 ? formattedHistory : [
          {
            id: 'h1',
            timestamp: new Date().toLocaleString(),
            action: 'No tasks completed yet',
            status: 'pending' as const,
          },
        ],
      };
      
      setSelectedAgent(agentData);
    }
  }, []);

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setSelectedAgent(null);
  }, []);

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
          onClick={resetDiagram}
          danger
        >
          Reset
        </Button>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
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

      <Modal
        title={selectedAgent ? `${selectedAgent.name} Details` : 'Agent Details'}
        open={isModalOpen}
        onCancel={handleCloseModal}
        footer={[
          <Button key="close" onClick={handleCloseModal}>
            Close
          </Button>,
        ]}
        width={700}
        className={isDarkMode ? 'dark-modal' : ''}
      >
        {selectedAgent && (
          <div>
            <Card style={{ marginBottom: 16, backgroundColor: isDarkMode ? '#1f1f1f' : '#fff' }}>
              <Title level={4}>{selectedAgent.name}</Title>
              <Tag color="blue" style={{ marginBottom: 12 }}>
                {selectedAgent.type}
              </Tag>
              <Paragraph>{selectedAgent.description}</Paragraph>
              
              <div style={{ marginTop: 16 }}>
                <Text strong>Capabilities:</Text>
                <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {selectedAgent.capabilities.map((capability, index) => (
                    <Tag key={index} color="cyan">
                      {capability}
                    </Tag>
                  ))}
                </div>
              </div>
            </Card>

            <Card title="History" style={{ backgroundColor: isDarkMode ? '#1f1f1f' : '#fff' }}>
              <Timeline
                items={selectedAgent.history.map((item) => ({
                  color:
                    item.status === 'success'
                      ? 'green'
                      : item.status === 'error'
                      ? 'red'
                      : 'gray',
                  children: (
                    <div>
                      <Text strong>{item.action}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        {item.timestamp}
                      </Text>
                      <Tag
                        color={
                          item.status === 'success'
                            ? 'success'
                            : item.status === 'error'
                            ? 'error'
                            : 'default'
                        }
                        style={{ marginLeft: 8 }}
                      >
                        {item.status}
                      </Tag>
                    </div>
                  ),
                }))}
              />
            </Card>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ArchitectureDiagram;
