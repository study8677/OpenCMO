import { useRef, useEffect, useCallback, useState, useMemo } from "react";
import ForceGraph3D from "react-force-graph-3d";
import * as THREE from "three";
import type { GraphData, GraphNode } from "../../api/graph";
import { useI18n } from "../../i18n";

/* ─── Light Elegant Color Palette ─── */
const NODE_COLORS: Record<string, number> = {
  brand: 0x6366f1,            // Indigo
  keyword: 0x0ea5e9,          // Sky blue
  discussion: 0xf59e0b,       // Amber
  serp: 0x10b981,             // Emerald
  competitor: 0xf43f5e,       // Rose
  competitor_keyword: 0xf97316, // Orange
};

const NODE_COLORS_CSS: Record<string, string> = {
  brand: "#6366f1",
  keyword: "#0ea5e9",
  discussion: "#f59e0b",
  serp: "#10b981",
  competitor: "#f43f5e",
  competitor_keyword: "#f97316",
};

const LINK_COLORS: Record<string, string> = {
  has_keyword: "rgba(99, 102, 241, 0.25)",
  has_discussion: "rgba(245, 158, 11, 0.25)",
  serp_rank: "rgba(16, 185, 129, 0.25)",
  competitor_of: "rgba(244, 63, 94, 0.35)",
  comp_keyword: "rgba(249, 115, 22, 0.25)",
  keyword_overlap: "rgba(225, 29, 72, 0.6)",
  expanded_from: "rgba(168, 85, 247, 0.35)", // Purple for expansion edges
};

const TYPE_LABELS_EN: Record<string, string> = {
  brand: "Brand",
  keyword: "Keyword",
  discussion: "Discussion",
  serp: "SERP Rank",
  competitor: "Competitor",
  competitor_keyword: "Competitor KW",
};

const TYPE_LABELS_ZH: Record<string, string> = {
  brand: "品牌",
  keyword: "关键词",
  discussion: "社区讨论",
  serp: "搜索排名",
  competitor: "竞品",
  competitor_keyword: "竞品关键词",
};

/* ─── Sizing ─── */
function getNodeSize(node: GraphNode): number {
  if (node.type === "brand") return 12;
  if (node.type === "competitor") return 9;
  if (node.type === "discussion") return 3 + Math.min((node.engagement ?? 0) / 30, 6);
  if (node.type === "keyword") return 5;
  if (node.type === "serp") return 4;
  return 3;
}

interface NewNodeData extends GraphNode {
  __isNew?: number; // timestamp when added
}

export function KnowledgeGraph({ data }: { data: GraphData }) {
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const { locale } = useI18n();
  const isZh = locale === "zh";
  const typeLabels = isZh ? TYPE_LABELS_ZH : TYPE_LABELS_EN;

  // Track previous nodes to detect new ones and animate them
  const prevNodesRef = useRef<Set<string>>(new Set());
  const animatedMeshesRef = useRef<any[]>([]);
  const animationFrameRef = useRef<number | undefined>(undefined);

  // Measure container
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const { width, height } = entries[0]!.contentRect;
      if (width > 0 && height > 0) setDimensions({ width, height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Update Data & detect newly added nodes
  const graphData = useMemo(() => {
    const currentNodes = new Set(data.nodes.map(n => String(n.id)));
    const hasHistory = prevNodesRef.current.size > 0;
    
    const nodes = data.nodes.map((n) => {
      const isNew = hasHistory && !prevNodesRef.current.has(String(n.id));
      return { 
        ...n, 
        __isNew: isNew ? Date.now() : undefined 
      } as NewNodeData;
    });

    prevNodesRef.current = currentNodes;
    
    return {
      nodes,
      links: data.links.map((l) => ({ ...l })),
    };
  }, [data]);

  // Handle graph auto-rotation & lighting customization
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg || graphData.nodes.length === 0) return;

    // Zoom to fit on initial load
    setTimeout(() => fg.zoomToFit(800, 80), 500);

    // Auto rotate
    const controls = fg.controls();
    if (controls) {
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.5;
    }

    // Adjust lighting for white background
    const scene = fg.scene();
    if (scene) {
      // Clean up previous custom lights if any
      scene.children = scene.children.filter((c: any) => !c.__customLight);

      // Add a bright, soft ambient light
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
      (ambientLight as any).__customLight = true;
      scene.add(ambientLight);

      // Add a directional light with soft shadows capability (for physical materials)
      const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
      dirLight.position.set(1, 2, 3);
      (dirLight as any).__customLight = true;
      scene.add(dirLight);
    }
  }, [graphData]);

  // Handle animation loop for new node pulses
  useEffect(() => {
    const renderLoop = () => {
      const now = Date.now();
      // Animate all pulse rings
      animatedMeshesRef.current.forEach(mesh => {
        // mesh.userData.startTime is stored when creating the mesh
        const elapsed = now - (mesh.userData.startTime || now);
        const cycle = (elapsed % 2000) / 2000; // 0 to 1 over 2 seconds
        
        // Scale from 1 to 2
        const scale = 1 + cycle;
        mesh.scale.set(scale, scale, scale);
        
        // Fade out as it expands
        if (mesh.material?.transparent) {
          mesh.material.opacity = 0.8 * (1 - cycle);
        }
      });
      animationFrameRef.current = requestAnimationFrame(renderLoop);
    };
    
    animationFrameRef.current = requestAnimationFrame(renderLoop);
    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, []);

  const handleNodeClick = useCallback((node: any) => {
    const fg = fgRef.current;
    if (fg) {
      const controls = fg.controls();
      if (controls) controls.autoRotate = false;
    }
    if (node.url) window.open(node.url, "_blank");
  }, []);

  /* ─── 3D Object Creation for Light elegant theme ─── */
  const createNodeObject = useCallback((node: any) => {
    const group = new THREE.Group();
    const color = NODE_COLORS[node.type] ?? 0x94a3b8;
    const size = getNodeSize(node as GraphNode);
    const n = node as NewNodeData;

    // Use MeshPhysicalMaterial for a polished, glassy "app-like" look
    const geo = new THREE.SphereGeometry(size, 32, 32);
    const mat = new THREE.MeshPhysicalMaterial({
      color,
      roughness: 0.15,
      transmission: 0.1,  // slight glass effect
      thickness: 1,
      clearcoat: 1.0,     // highly polished
      clearcoatRoughness: 0.1,
    });
    const sphere = new THREE.Mesh(geo, mat);

    // Depth-based styling for expansion-discovered nodes
    const depth = (node as any).depth ?? 0;
    if (depth > 0) {
      const depthScale = Math.max(0.6, 1.0 - depth * 0.1);
      sphere.scale.setScalar(depthScale);
      mat.opacity = Math.max(0.4, 1.0 - depth * 0.12);
      mat.transparent = true;
    }

    group.add(sphere);

    // Frontier indicator: wireframe ring for unexplored expansion nodes
    if (!(node as any).explored && depth > 0) {
      const ringGeo = new THREE.TorusGeometry(size * 0.8 + 2, 0.3, 8, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0xa855f7,
        transparent: true,
        opacity: 0.5,
        wireframe: true,
      });
      const frontierRing = new THREE.Mesh(ringGeo, ringMat);
      frontierRing.rotation.x = Math.PI / 2;
      group.add(frontierRing);
    }

    // If Brand node, add an elegant double ring
    if (n.type === "brand") {
      const ringGeo = new THREE.TorusGeometry(size + 3, 0.4, 16, 64);
      const ringMat = new THREE.MeshStandardMaterial({ 
        color: 0x6366f1, 
        roughness: 0.2, 
        metalness: 0.8 
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      
      const ringGeo2 = new THREE.TorusGeometry(size + 5, 0.2, 16, 64);
      const ringMat2 = new THREE.MeshStandardMaterial({ 
        color: 0x818cf8, 
        transparent: true,
        opacity: 0.6
      });
      const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
      
      // Rotate them slightly so they aren't completely flat
      ring.rotation.x = Math.PI / 3;
      ring2.rotation.y = Math.PI / 3;
      
      group.add(ring);
      group.add(ring2);
    }

    // If it's a NEW node, add an animated pulse effect
    if (n.__isNew) {
      // Only keep bubbling for a minute or so to not degrade performance long term
      const age = Date.now() - n.__isNew;
      if (age < 60000) {
        const pulseGeo = new THREE.SphereGeometry(size + 0.5, 32, 32);
        const pulseMat = new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.8,
          side: THREE.BackSide,
        });
        const pulseMesh = new THREE.Mesh(pulseGeo, pulseMat);
        pulseMesh.userData = { startTime: n.__isNew };
        group.add(pulseMesh);
        
        // Save to animated meshes array
        animatedMeshesRef.current.push(pulseMesh);
        
        // Clean up when the object is removed
        group.addEventListener('removed', () => {
          animatedMeshesRef.current = animatedMeshesRef.current.filter(m => m !== pulseMesh);
        });
      }
    }

    return group;
  }, []);

  const getNodeThreeLabel = useCallback((node: any) => {
    const n = node as GraphNode;
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d")!;
    const text = n.label;
    const fontSize = n.type === "brand" ? 36 : 24;
    
    // Measure text to size canvas accurately
    ctx.font = `${n.type === "brand" ? "bold " : ""}${fontSize}px Inter, system-ui, sans-serif`;
    const textWidth = ctx.measureText(text).width;
    canvas.width = textWidth + 32;
    canvas.height = fontSize + 24;
    
    // Draw text with shadow (looks better on light bg)
    ctx.font = `${n.type === "brand" ? "bold " : ""}${fontSize}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    
    // Text shadow for legibility over links
    ctx.shadowColor = "rgba(255, 255, 255, 0.8)";
    ctx.shadowBlur = 6;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
    
    // Fill text (dark slate color instead of white)
    ctx.fillStyle = n.type === "brand" ? "#312e81" : "#1e293b";
    
    if (n.type === "brand") {
      ctx.fillStyle = "#4f46e5"; // Indigo for brand text
    } else if ((node as NewNodeData).__isNew) {
      ctx.fillStyle = NODE_COLORS_CSS[n.type] ?? "#1e293b"; // Colored text for new nodes to grab attention
    }
    
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);

    const texture = new THREE.CanvasTexture(canvas);
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.minFilter = THREE.LinearFilter; // for crispness
    
    const spriteMat = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthWrite: false, // Prevents z-fighting
    });
    
    const sprite = new THREE.Sprite(spriteMat);
    const scaleFactor = n.type === "brand" ? 1.0 : 0.6;
    sprite.scale.set(canvas.width * 0.08 * scaleFactor, canvas.height * 0.08 * scaleFactor, 1);
    sprite.position.set(0, getNodeSize(n) + 5, 0); // Position slightly above the node
    return sprite;
  }, []);

  const nodeThreeObject = useCallback((node: any) => {
    const group = createNodeObject(node);
    const label = getNodeThreeLabel(node);
    group.add(label);
    return group;
  }, [createNodeObject, getNodeThreeLabel]);

  // Link colors & properties
  const getLinkColor = useCallback((link: any) => {
    return LINK_COLORS[link.type] ?? "rgba(203, 213, 225, 0.4)"; // Slate 300
  }, []);

  const getLinkWidth = useCallback((link: any) => {
    return link.type === "keyword_overlap" ? 2.5 : 0.8;
  }, []);

  const getLinkParticles = useCallback((link: any) => {
    if (link.type === "keyword_overlap") return 4;
    if (link.type === "competitor_of") return 3;
    return 0;
  }, []);
  
  const getLinkParticleColor = useCallback((link: any) => {
    if (link.type === "keyword_overlap") return "#e11d48"; // Rose 600
    if (link.type === "competitor_of") return "#f43f5e"; // Rose 500
    return "#94a3b8";
  }, []);

  // HTML Node Label Tooltip (Light Theme Card)
  const getNodeLabelHtml = useCallback((node: any) => {
    const n = node as NewNodeData;
    const typeName = typeLabels[n.type] ?? n.type;
    const isNew = !!n.__isNew;
    
    let html = `<div style="
      background: rgba(255,255,255,0.9);
      backdrop-filter: blur(12px);
      color: #1e293b;
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 13px;
      max-width: 280px;
      line-height: 1.5;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
      border: 1px solid rgba(226, 232, 240, 0.8);
      font-family: Inter, system-ui, sans-serif;
    ">`;
    
    html += `<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">`;
    html += `<div style="font-size:15px; font-weight:700; color: #0f172a;">${n.label}</div>`;
    if (isNew) {
      html += `<span style="background: linear-gradient(135deg, #a855f7, #ef4444); -webkit-background-clip: text; color: transparent; font-size:11px; font-weight:700; letter-spacing:0.5px; animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;">NEW!</span>`;
    }
    html += `</div>`;
    
    // Badge for type
    const badgeColor = NODE_COLORS_CSS[n.type] || "#94a3b8";
    html += `<div style="display:inline-block; padding: 2px 8px; border-radius: 999px; background: ${badgeColor}15; color: ${badgeColor}; font-size: 11px; font-weight: 600; margin-bottom: 8px; border: 1px solid ${badgeColor}30;">${typeName}</div>`;
    
    if (n.platform) html += `<div style="color: #64748b; margin-top: 4px; display:flex; justify-content:space-between;"><span>${isZh ? "平台" : "Platform"}</span> <span style="font-weight:500; color:#334155;">${n.platform}</span></div>`;
    if (n.engagement != null) html += `<div style="color: #64748b; margin-top: 4px; display:flex; justify-content:space-between;"><span>${isZh ? "互动分" : "Engagement"}</span> <span style="font-weight:600; color:#334155;">${n.engagement}</span></div>`;
    if (n.comments != null) html += `<div style="color: #64748b; margin-top: 4px; display:flex; justify-content:space-between;"><span>${isZh ? "评论数" : "Comments"}</span> <span style="font-weight:500; color:#334155;">${n.comments}</span></div>`;
    if (n.position != null) html += `<div style="color: #64748b; margin-top: 4px; display:flex; justify-content:space-between;"><span>${isZh ? "排名" : "Rank"}</span> <span style="font-weight:600; color:#10b981;">#${n.position}</span></div>`;
    if (n.url) html += `<div style="color: #6366f1; margin-top: 8px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:12px;">${n.url}</div>`;
    html += `</div>`;
    return html;
  }, [typeLabels, isZh]);

  return (
    <div className="relative rounded-2xl border border-zinc-200/50 bg-white shadow-xl overflow-hidden ring-1 ring-zinc-900/5">
      {/* Background Gradient to make it look premium but light */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 opacity-80 pointer-events-none" />

      {/* Legend */}
      <div className="absolute top-4 left-4 z-10 flex flex-wrap gap-2.5 rounded-xl bg-white/70 backdrop-blur-xl px-4 py-3 shadow-lg ring-1 ring-zinc-200/60 transition-all">
        {Object.entries(NODE_COLORS_CSS).map(([type, color]) => (
          <div key={type} className="flex items-center gap-2">
            <span
              className="inline-block h-3 w-3 rounded-full shadow-sm"
              style={{ backgroundColor: color }}
            />
            <span className="text-[11px] font-semibold text-slate-700 tracking-wide uppercase">
              {typeLabels[type] ?? type}
            </span>
          </div>
        ))}
      </div>

      {/* Controls hint */}
      <div className="absolute bottom-4 left-4 z-10 rounded-xl bg-white/70 px-3 py-2 text-[11px] font-medium text-slate-500 backdrop-blur-xl shadow-sm ring-1 ring-zinc-200/50">
        {isZh ? "🖱 拖拽旋转 · 滚轮缩放 · 右键平移 · 点击节点打开链接" : "🖱 Drag to rotate · Scroll to zoom · Right-click to pan · Click nodes"}
      </div>

      {/* 3D Graph container */}
      <div ref={containerRef} style={{ width: "100%", height: 600, zIndex: 1 }}>
        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          width={dimensions.width}
          height={600}
          backgroundColor="rgba(0,0,0,0)" // Transparent to show the CSS gradient behind
          nodeThreeObject={nodeThreeObject}
          nodeLabel={getNodeLabelHtml}
          onNodeClick={handleNodeClick}
          linkColor={getLinkColor}
          linkWidth={getLinkWidth}
          linkOpacity={0.8}
          linkDirectionalParticles={getLinkParticles}
          linkDirectionalParticleColor={getLinkParticleColor}
          linkDirectionalParticleWidth={2}
          linkDirectionalParticleSpeed={0.008}
          linkCurvature={0.15}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.4}
          cooldownTicks={100}
          enableNodeDrag={true}
          enableNavigationControls={true}
          showNavInfo={false}
        />
      </div>
    </div>
  );
}
