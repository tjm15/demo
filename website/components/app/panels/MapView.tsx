import React, { useEffect, useRef } from 'react';
import maplibregl, { Map } from 'maplibre-gl';

interface MapViewProps {
  data: {
    lat?: number;
    lng?: number;
    zoom?: number;
  };
}

export function MapView({ data }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const { lat = 51.5074, lng = -0.1278, zoom = 13 } = data || {};

    // Initialize map once
    if (!mapRef.current) {
      mapRef.current = new maplibregl.Map({
        container: containerRef.current,
        style: {
          version: 8,
          sources: {
            osm: {
              type: 'raster',
              tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
              tileSize: 256,
              attribution:
                '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            },
          },
          layers: [
            {
              id: 'osm',
              type: 'raster',
              source: 'osm',
            },
          ],
        },
        center: [lng, lat],
        zoom,
      });
    } else {
      mapRef.current.setCenter([lng, lat]);
      mapRef.current.setZoom(zoom);
    }

    // Add a marker at the site location
    const marker = new maplibregl.Marker({ color: '#329c85' })
      .setLngLat([lng, lat])
      .addTo(mapRef.current as Map);

    return () => {
      marker.remove();
    };
  }, [data?.lat, data?.lng, data?.zoom]);

  return (
    <div className="bg-[color:var(--panel)] rounded-xl border border-[color:var(--edge)] shadow-sm">
      <div className="p-4 border-b border-[color:var(--edge)]">
        <h3 className="text-sm font-semibold text-[color:var(--ink)]">Map</h3>
      </div>
      <div ref={containerRef} style={{ height: 360 }} />
    </div>
  );
}
