import React, { useMemo } from 'react';
import { Network, File, Box, ShieldAlert, Zap } from 'lucide-react';
import type { KnowledgeGraph, RCAReport } from '../types';

interface GraphViewProps {
  graph: KnowledgeGraph;
  rca: RCAReport;
  status: 'idle' | 'running' | 'completed' | 'failed';
}

export const GraphView: React.FC<GraphViewProps> = ({ graph, rca, status }) => {
  // We structure the nodes into columns: File, Class, Function
  const layout = useMemo(() => {
    if (!graph.nodes || graph.nodes.length === 0) return { nodes: [], edges: [] };

    // Separate nodes by type
    const files = graph.nodes.filter(n => n.type === 'file');
    const classes = graph.nodes.filter(n => n.type === 'class');
    const functions = graph.nodes.filter(n => n.type === 'function');

    const width = 800;
    const height = 300;

    const coords: Record<string, { x: number; y: number }> = {};
    const processedNodes: any[] = [];

    // Calculate layout coords
    // 1. Files: x = 100
    files.forEach((node, i) => {
      const y = files.length > 1 
        ? 50 + (i * (height - 100)) / (files.length - 1)
        : height / 2;
      coords[node.id] = { x: 120, y };
      processedNodes.push({ ...node, x: 120, y });
    });

    // 2. Classes: x = 380
    classes.forEach((node, i) => {
      const y = classes.length > 1
        ? 50 + (i * (height - 100)) / (classes.length - 1)
        : height / 2;
      coords[node.id] = { x: 400, y };
      processedNodes.push({ ...node, x: 400, y });
    });

    // 3. Functions: x = 680
    functions.forEach((node, i) => {
      const y = functions.length > 1
        ? 30 + (i * (height - 60)) / (functions.length - 1)
        : height / 2;
      coords[node.id] = { x: 680, y };
      processedNodes.push({ ...node, x: 680, y });
    });

    // Handle edges coords
    const processedEdges = graph.edges
      .map(edge => {
        const sourceCoord = coords[edge.source];
        const targetCoord = coords[edge.target];
        if (sourceCoord && targetCoord) {
          return {
            ...edge,
            x1: sourceCoord.x,
            y1: sourceCoord.y,
            x2: targetCoord.x,
            y2: targetCoord.y
          };
        }
        return null;
      })
      .filter(Boolean) as any[];

    return { nodes: processedNodes, edges: processedEdges };
  }, [graph]);

  // Check if a node is part of the validated root cause
  const isRootCauseNode = (nodeId: string, label: string) => {
    if (!rca || !rca.affected_component) return false;
    const component = rca.affected_component.toLowerCase();
    
    // Check if node is the file mentioned or the function mentioned
    if (nodeId.toLowerCase().includes(component)) return true;
    if (label.toLowerCase() === component.split('->')[1]?.trim().split('(')[0]?.toLowerCase()) return true;
    if (label.toLowerCase() === component.split('->')[0]?.trim().toLowerCase()) return true;
    
    return false;
  };

  return (
    <div className="glass-panel p-5 mb-6 flex flex-col h-[400px]">
      <div className="flex items-center gap-2 mb-4 border-b border-borderDark pb-3">
        <Network className="w-5 h-5 text-indigo-400" />
        <h2 className="text-sm font-semibold tracking-wider font-mono">SOFTWARE KNOWLEDGE GRAPH</h2>
        {rca && rca.affected_component && (
          <span className="ml-auto flex items-center gap-1 text-[10px] text-accentRed font-mono border border-red-900/60 bg-red-950/20 px-2 py-0.5 rounded">
            <ShieldAlert className="w-3 h-3" />
            ROOT CAUSE ISOLATED
          </span>
        )}
      </div>

      <div className="flex-1 bg-black/30 border border-borderDark rounded-lg overflow-hidden relative flex items-center justify-center">
        {layout.nodes.length > 0 ? (
          <svg className="w-full h-full min-h-[280px]" viewBox="0 0 800 300" preserveAspectRatio="xMidYMid meet">
            {/* Defs for gradients & markers */}
            <defs>
              <marker
                id="arrow"
                viewBox="0 0 10 10"
                refX="18"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#26213A" />
              </marker>
              <linearGradient id="purple-green" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#10B981" stopOpacity="0.4" />
              </linearGradient>
            </defs>

            {/* Draw Edges */}
            {layout.edges.map((edge, idx) => {
              const isCall = edge.type === 'calls';
              const strokeColor = isCall ? 'url(#purple-green)' : '#26213A';
              const strokeDash = isCall ? '3,3' : 'none';

              return (
                <g key={idx}>
                  <line
                    x1={edge.x1}
                    y1={edge.y1}
                    x2={edge.x2}
                    y2={edge.y2}
                    stroke={strokeColor}
                    strokeWidth={isCall ? 1.5 : 1}
                    strokeDasharray={strokeDash}
                    markerEnd="url(#arrow)"
                  />
                  {/* Small relation label in the middle of line */}
                  <text
                    x={(edge.x1 + edge.x2) / 2}
                    y={(edge.y1 + edge.y2) / 2 - 4}
                    fill="#4B5563"
                    fontSize="7"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    {edge.type}
                  </text>
                </g>
              );
            })}

            {/* Draw Nodes */}
            {layout.nodes.map((node) => {
              const isCulprit = isRootCauseNode(node.id, node.label);
              
              // Styles based on types and culprit status
              let fillColor = '#13111C';
              let strokeColor = '#26213A';
              let textGlow = '';
              let Icon = File;

              if (node.type === 'file') {
                fillColor = '#10B981';
                strokeColor = '#34D399';
                Icon = File;
              } else if (node.type === 'class') {
                fillColor = '#8B5CF6';
                strokeColor = '#A78BFA';
                Icon = Box;
              } else if (node.type === 'function') {
                fillColor = '#3B82F6';
                strokeColor = '#60A5FA';
                Icon = Zap;
              }

              if (isCulprit) {
                fillColor = '#EF4444';
                strokeColor = '#F87171';
                textGlow = 'glow-text-red';
              }

              return (
                <g key={node.id} className="cursor-pointer group">
                  {/* Culprit Warning Radar */}
                  {isCulprit && (
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r="22"
                      fill="none"
                      stroke="#EF4444"
                      strokeWidth="1.5"
                      className="animate-ping"
                      opacity="0.3"
                    />
                  )}
                  
                  {/* Node Background Circle */}
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r="12"
                    fill="#0B0A0F"
                    stroke={strokeColor}
                    strokeWidth={isCulprit ? 2.5 : 1.5}
                    className="group-hover:stroke-purple-400 transition-colors"
                  />

                  {/* Icon Node Dot */}
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r="8"
                    fill={fillColor}
                    opacity="0.85"
                  />

                  {/* Node Label Text */}
                  <text
                    x={node.x}
                    y={node.y + 24}
                    fill={isCulprit ? '#EF4444' : '#E5E7EB'}
                    fontSize="9"
                    fontWeight={isCulprit ? 'bold' : 'normal'}
                    fontFamily="monospace"
                    textAnchor="middle"
                    className="group-hover:fill-purple-400"
                  >
                    {node.label}
                  </text>
                  
                  {/* Secondary type indicator */}
                  <text
                    x={node.x}
                    y={node.y - 18}
                    fill="#4B5563"
                    fontSize="6"
                    fontFamily="monospace"
                    textAnchor="middle"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    {node.type.toUpperCase()}
                  </text>
                </g>
              );
            })}
          </svg>
        ) : (
          <div className="flex flex-col items-center justify-center text-textMuted/40 font-mono text-center">
            <Network className="w-10 h-10 mb-2 opacity-25" />
            <p>Index mapping queue empty.</p>
            <p className="text-[10px] mt-1">Repository Intel Agent will index codebase on deploy.</p>
          </div>
        )}
      </div>
    </div>
  );
};
