import React from "react";
import { usePrefersReducedMotion } from "../hooks/usePrefersReducedMotion";
import { theme } from "../constants";

export function AmbientNetwork({ className = "" }: { className?: string }) {
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);
  const reduced = usePrefersReducedMotion();

  React.useEffect(() => {
    const cv = canvasRef.current; if (!cv) return;
    const ctx = cv.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    const DPR = Math.min(window.devicePixelRatio || 1, 2);
    const nodes = Array.from({ length: 36 }, () => ({
      x: Math.random(), y: Math.random(),
      vx: (Math.random() - 0.5) * 0.02,
      vy: (Math.random() - 0.5) * 0.02,
    }));

    const resize = () => {
      if (!cv) return;
      const r = cv.getBoundingClientRect();
      cv.width = r.width * DPR;
      cv.height = r.height * DPR;
      ctx.setTransform(DPR,0,0,DPR,0,0);
    };
    
    window.addEventListener("resize", resize);
    resize();

    const BRAND = getComputedStyle(document.documentElement).getPropertyValue("--brand").trim() || theme.brand;
    const hexBrand = BRAND.replace('#','');
    const rBrand = parseInt(hexBrand.substring(0,2),16);
    const gBrand = parseInt(hexBrand.substring(2,4),16);
    const bBrand = parseInt(hexBrand.substring(4,6),16);
    
    const EDGE = getComputedStyle(document.documentElement).getPropertyValue("--edge").trim() || theme.edge;
    const hexEdge = EDGE.replace('#','');
    const rEdge = parseInt(hexEdge.substring(0,2),16);
    const gEdge = parseInt(hexEdge.substring(2,4),16);
    const bEdge = parseInt(hexEdge.substring(4,6),16);

    const render = () => {
      if (!cv) return;
      const w = cv.width / DPR, h = cv.height / DPR;
      ctx.clearRect(0,0,w,h);
      
      // Grid
      ctx.strokeStyle = `rgba(${rEdge},${gEdge},${bEdge},0.5)`;
      ctx.lineWidth = 1;
      for (let gx = 0; gx < w; gx += 40) { ctx.beginPath(); ctx.moveTo(gx,0); ctx.lineTo(gx,h); ctx.stroke(); }
      for (let gy = 0; gy < h; gy += 40) { ctx.beginPath(); ctx.moveTo(0,gy); ctx.lineTo(w,gy); ctx.stroke(); }

      nodes.forEach(n => { if (!reduced) { n.x += n.vx * 0.04; n.y += n.vy * 0.04; } if (n.x < 0 || n.x > 1) n.vx *= -1; if (n.y < 0 || n.y > 1) n.vy *= -1; });

      // Connections
      for (let i=0;i<nodes.length;i++) for (let j=i+1;j<nodes.length;j++){
        const a = nodes[i], b2 = nodes[j]; const dx=a.x-b2.x, dy=a.y-b2.y; const d2=dx*dx+dy*dy;
        if (d2 < 0.05) { 
            const alpha = 0.14 * (1 - d2/0.05); 
            ctx.strokeStyle = `rgba(${rBrand},${gBrand},${bBrand},${alpha})`; 
            ctx.beginPath(); 
            ctx.moveTo(a.x*w,a.y*h); 
            ctx.lineTo(b2.x*w,b2.y*h); 
            ctx.stroke(); 
        }
      }
      
      // Nodes
      nodes.forEach(n => { 
          ctx.fillStyle = `rgba(${rBrand},${gBrand},${bBrand},0.22)`; 
          ctx.beginPath(); 
          ctx.arc(n.x*w,n.y*h,2.1,0,Math.PI*2); 
          ctx.fill(); 
      });

      raf = requestAnimationFrame(render);
    };
    render();
    
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [reduced]);

  return <canvas ref={canvasRef} className={`${className} block w-full h-full`} aria-hidden="true" />;
}