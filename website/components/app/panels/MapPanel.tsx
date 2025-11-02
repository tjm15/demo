import React from 'react';
import { motion } from 'framer-motion';
import { MapPin, Layers } from 'lucide-react';

interface MapPanelProps {
  data: {
    center?: { lat: number; lng: number };
    constraints?: Array<{
      type: string;
      name: string;
      impact: string;
      geometry?: any;
    }>;
  };
}

export function MapPanel({ data }: MapPanelProps) {
  const { center, constraints = [] } = data;

  // For now, static map with Leaflet-style display
  // In production, integrate react-leaflet or mapbox-gl
  const mapUrl = center
    ? `https://www.openstreetmap.org/export/embed.html?bbox=${center.lng - 0.01},${center.lat - 0.01},${center.lng + 0.01},${center.lat + 0.01}&layer=mapnik&marker=${center.lat},${center.lng}`
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm overflow-hidden"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-[color:var(--edge)] bg-[color:var(--surface)]/50">
        <div className="flex items-center gap-2">
          <MapPin className="w-5 h-5 text-[color:var(--accent)]" />
          <h3 className="text-lg font-semibold text-[color:var(--ink)]">Site Map</h3>
        </div>
        {center && (
          <p className="text-sm text-[color:var(--muted)] mt-1">
            {center.lat.toFixed(6)}, {center.lng.toFixed(6)}
          </p>
        )}
      </div>

      {/* Map Display */}
      <div className="relative">
        {mapUrl ? (
          <iframe
            src={mapUrl}
            className="w-full h-[400px] border-0"
            title="Site location map"
          />
        ) : (
          <div className="flex items-center justify-center h-[400px] bg-[color:var(--surface)]">
            <div className="text-center text-[color:var(--muted)]">
              <Layers className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No location data available</p>
              <p className="text-sm mt-1">Provide site coordinates to display map</p>
            </div>
          </div>
        )}
      </div>

      {/* Constraint Legend */}
      {constraints.length > 0 && (
        <div className="px-6 py-4 border-t border-[color:var(--edge)] bg-[color:var(--surface)]/30">
          <h4 className="text-sm font-semibold text-[color:var(--ink)] mb-3">
            Spatial Constraints ({constraints.length})
          </h4>
          <div className="space-y-2 max-h-[200px] overflow-y-auto">
            {constraints.map((c, i) => (
              <div
                key={i}
                className="flex items-start gap-3 p-2 rounded-lg bg-[color:var(--panel)] border border-[color:var(--edge)]"
              >
                <div
                  className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${
                    c.impact === 'high'
                      ? 'bg-red-500'
                      : c.impact === 'moderate'
                      ? 'bg-yellow-500'
                      : 'bg-blue-500'
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-[color:var(--ink)]">{c.name}</div>
                  <div className="text-xs text-[color:var(--muted)] capitalize">{c.type}</div>
                </div>
                <div
                  className={`text-xs font-medium px-2 py-1 rounded ${
                    c.impact === 'high'
                      ? 'bg-red-100 text-red-700'
                      : c.impact === 'moderate'
                      ? 'bg-yellow-100 text-yellow-700'
                      : 'bg-blue-100 text-blue-700'
                  }`}
                >
                  {c.impact}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
