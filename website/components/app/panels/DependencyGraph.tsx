import React, { useEffect, useRef } from 'react';
import { Network, Maximize2 } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: 'evidence' | 'policy';
  subtype?: string;
}

interface GraphEdge {
  from: string;
  to: string;
  strength: 'core' | 'supporting' | 'tangential';
  rationale?: string;
}

interface DependencyGraphProps {
  data: {
    nodes: GraphNode[];
    edges: GraphEdge[];
  };
  onSelectNode?: (nodeId: string, type: 'evidence' | 'policy') => void;
}

const STRENGTH_COLORS = {
  core: '#22c55e',
  supporting: '#3b82f6',
  tangential: '#9ca3af',
};

export function DependencyGraph({ data, onSelectNode }: DependencyGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !data.nodes.length) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = containerRef.current?.getBoundingClientRect();
    if (rect) {
      canvas.width = rect.width;
      canvas.height = Math.max(400, rect.height);
    }

    // Simple force-directed layout simulation
    const nodeMap = new Map<string, { x: number; y: number; vx: number; vy: number; node: GraphNode }>();
    
    // Initialize nodes with positions
    data.nodes.forEach((node, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      const radius = Math.min(canvas.width, canvas.height) * 0.3;
      nodeMap.set(node.id, {
        x: canvas.width / 2 + Math.cos(angle) * radius,
        y: canvas.height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        node,
      });
    });

    // Simple physics simulation (just a few iterations)
    for (let iter = 0; iter < 50; iter++) {
      // Repulsion between nodes
      nodeMap.forEach((a) => {
        nodeMap.forEach((b) => {
          if (a === b) return;
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 100 / (dist * dist);
          a.vx -= (dx / dist) * force;
          a.vy -= (dy / dist) * force;
        });
      });

      // Attraction along edges
      data.edges.forEach((edge) => {
        const a = nodeMap.get(edge.from);
        const b = nodeMap.get(edge.to);
        if (!a || !b) return;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = dist * 0.01;
        a.vx += (dx / dist) * force;
        a.vy += (dy / dist) * force;
        b.vx -= (dx / dist) * force;
        b.vy -= (dy / dist) * force;
      });

      // Apply velocity with damping
      nodeMap.forEach((n) => {
        n.x += n.vx;
        n.y += n.vy;
        n.vx *= 0.8;
        n.vy *= 0.8;
        // Keep in bounds
        n.x = Math.max(50, Math.min(canvas.width - 50, n.x));
        n.y = Math.max(50, Math.min(canvas.height - 50, n.y));
      });
    }

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw edges
    data.edges.forEach((edge) => {
      const from = nodeMap.get(edge.from);
      const to = nodeMap.get(edge.to);
      if (!from || !to) return;

      ctx.strokeStyle = STRENGTH_COLORS[edge.strength];
      ctx.lineWidth = edge.strength === 'core' ? 3 : edge.strength === 'supporting' ? 2 : 1;
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();

      // Arrow head
      const angle = Math.atan2(to.y - from.y, to.x - from.x);
      const headlen = 10;
      ctx.beginPath();
      ctx.moveTo(to.x, to.y);
      ctx.lineTo(
        to.x - headlen * Math.cos(angle - Math.PI / 6),
        to.y - headlen * Math.sin(angle - Math.PI / 6)
      );
      ctx.lineTo(
        to.x - headlen * Math.cos(angle + Math.PI / 6),
        to.y - headlen * Math.sin(angle + Math.PI / 6)
      );
      ctx.closePath();
      ctx.fillStyle = STRENGTH_COLORS[edge.strength];
      ctx.fill();
    });

    // Draw nodes
    nodeMap.forEach(({ x, y, node }) => {
      const isEvidence = node.type === 'evidence';
      const radius = 8;

      // Node circle
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = isEvidence ? '#8b5cf6' : '#3b82f6';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Label
      ctx.fillStyle = '#1f2937';
      ctx.font = '11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(node.label.substring(0, 20), x, y + radius + 14);
    });

  }, [data]);

  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-[color:var(--accent)]" />
          <h3 className="text-lg font-semibold text-[color:var(--ink)]">Dependency Graph</h3>
          <span className="text-sm text-[color:var(--muted)]">
            ({data.nodes.length} nodes, {data.edges.length} links)
          </span>
        </div>
        <button className="p-2 rounded-lg border border-[color:var(--edge)] bg-[color:var(--surface)] text-[color:var(--muted)] hover:border-[color:var(--accent)] hover:text-[color:var(--accent)] transition-colors">
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mb-4 p-3 rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)]">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span className="text-[color:var(--muted)]">Evidence</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span className="text-[color:var(--muted)]">Policy</span>
          </div>
        </div>
        <div className="h-4 w-px bg-[color:var(--edge)]"></div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-green-500"></div>
            <span className="text-[color:var(--muted)]">Core</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-blue-500"></div>
            <span className="text-[color:var(--muted)]">Supporting</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-gray-400"></div>
            <span className="text-[color:var(--muted)]">Tangential</span>
          </div>
        </div>
      </div>

      {/* Graph Canvas */}
      <div ref={containerRef} className="relative w-full h-[400px] rounded-lg bg-[color:var(--surface)] border border-[color:var(--edge)] overflow-hidden">
        {data.nodes.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-[color:var(--muted)]">
            <div className="text-center">
              <Network className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm">No dependencies to display</p>
            </div>
          </div>
        ) : (
          <canvas ref={canvasRef} className="w-full h-full" />
        )}
      </div>

      {/* Stats */}
      {data.nodes.length > 0 && (
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <div className="p-3 rounded-lg bg-purple-50 border border-purple-200">
            <div className="text-2xl font-bold text-purple-700">
              {data.nodes.filter((n) => n.type === 'evidence').length}
            </div>
            <div className="text-xs text-purple-600 mt-1">Evidence Items</div>
          </div>
          <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
            <div className="text-2xl font-bold text-blue-700">
              {data.nodes.filter((n) => n.type === 'policy').length}
            </div>
            <div className="text-xs text-blue-600 mt-1">Policies</div>
          </div>
          <div className="p-3 rounded-lg bg-green-50 border border-green-200">
            <div className="text-2xl font-bold text-green-700">{data.edges.length}</div>
            <div className="text-xs text-green-600 mt-1">Connections</div>
          </div>
        </div>
      )}
    </div>
  );
}
