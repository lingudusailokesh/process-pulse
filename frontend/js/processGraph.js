/**
 * ProcessPulse Cytoscape.js Process Flow (DFG) Visualizer
 */

let cyInstance = null;

export function renderProcessGraph(containerId, dfgData, onNodeClickCallback) {
  const container = document.getElementById(containerId);
  if (!container || !dfgData || !dfgData.nodes) return;

  // Convert DFG nodes into Cytoscape elements
  const elements = [];

  dfgData.nodes.forEach(node => {
    let nodeBg = '#1e293b';
    let borderColor = '#38bdf8';
    
    if (node.is_start) {
      borderColor = '#86bc25';
      nodeBg = '#162818';
    } else if (node.is_end) {
      borderColor = '#10b981';
      nodeBg = '#132e27';
    } else if (node.is_bottleneck) {
      borderColor = '#f43f5e';
      nodeBg = '#371720';
    }

    elements.push({
      data: {
        id: node.id,
        label: `${node.label}\n(${node.median_duration_hours}h | ${node.unique_cases_count} cases, ${node.execution_count} events)`,
        raw: node,
        bgColor: nodeBg,
        borderColor: borderColor,
        borderWidth: node.is_bottleneck ? 3 : 2
      }
    });
  });

  // Convert DFG edges
  dfgData.edges.forEach(edge => {
    const isLoop = edge.is_rework_loop;
    elements.push({
      data: {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: `${edge.avg_transition_hours}h (${edge.transition_count})`,
        lineColor: isLoop ? '#f43f5e' : '#64748b',
        lineStyle: isLoop ? 'dashed' : 'solid',
        targetArrowColor: isLoop ? '#f43f5e' : '#64748b',
        width: Math.min(6, Math.max(2, edge.transition_count / 80)),
        raw: edge
      }
    });
  });

  if (cyInstance) {
    cyInstance.destroy();
  }

  // Initialize Cytoscape with smooth pointer-focused zooming and full canvas navigation
  cyInstance = cytoscape({
    container: container,
    elements: elements,
    userZoomingEnabled: true,    // Allows mouse wheel / trackpad scroll-to-zoom at cursor position
    wheelSensitivity: 0.12,      // Gentle, smooth, non-jarring zoom rate
    userPanningEnabled: true,    // Allows grabbing and panning the canvas in any direction
    boxSelectionEnabled: false,
    minZoom: 0.25,               // Allows wide macro perspective
    maxZoom: 3.5,                // Allows close inspection of specific nodes & loop metrics
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-wrap': 'wrap',
          'color': '#f8fafc',
          'font-size': '10px',
          'font-family': 'Inter, sans-serif',
          'background-color': 'data(bgColor)',
          'border-color': 'data(borderColor)',
          'border-width': 'data(borderWidth)',
          'width': '132px',
          'height': '52px',
          'shape': 'roundrectangle',
          'text-max-width': '122px',
          'transition-property': 'background-color, border-color, width, height',
          'transition-duration': '0.2s'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 'data(width)',
          'line-color': 'data(lineColor)',
          'line-style': 'data(lineStyle)',
          'target-arrow-color': 'data(targetArrowColor)',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'font-size': '9px',
          'color': '#94a3b8',
          'text-rotation': 'autorotate',
          'text-background-color': '#0d1321',
          'text-background-opacity': 0.85,
          'text-background-padding': '2px'
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-color': '#10b981',
          'border-width': 3,
          'shadow-blur': 14,
          'shadow-color': '#10b981',
          'shadow-opacity': 0.7
        }
      }
    ],
    layout: {
      name: 'breadthfirst',
      directed: true,
      padding: 30,
      spacingFactor: 1.2,
      avoidOverlap: true,
      fit: true
    }
  });

  // Guarantee clean centering on initial load and layout finish
  cyInstance.on('layoutstop', () => {
    if (cyInstance) {
      cyInstance.resize();
      fitProcessGraph(false);
    }
  });

  // Double-click empty canvas to instantly re-center
  cyInstance.on('dblclick', function(e) {
    if (e.target === cyInstance) {
      fitProcessGraph(true);
    }
  });

  // Bind Locate / Fit Button (Prominent Green Reset)
  const fitBtn = document.getElementById('btn-cy-fit');
  if (fitBtn) {
    fitBtn.onclick = () => {
      fitProcessGraph(true);
    };
  }

  // Bind Zoom In (at canvas center)
  const zoomInBtn = document.getElementById('btn-cy-zoom-in');
  if (zoomInBtn) {
    zoomInBtn.onclick = () => {
      if (cyInstance) {
        cyInstance.animate({
          zoom: Math.min(cyInstance.zoom() * 1.3, 3.5),
          renderedPosition: { x: cyInstance.width() / 2, y: cyInstance.height() / 2 },
          duration: 200
        });
      }
    };
  }

  // Bind Zoom Out (at canvas center)
  const zoomOutBtn = document.getElementById('btn-cy-zoom-out');
  if (zoomOutBtn) {
    zoomOutBtn.onclick = () => {
      if (cyInstance) {
        cyInstance.animate({
          zoom: Math.max(cyInstance.zoom() / 1.3, 0.25),
          renderedPosition: { x: cyInstance.width() / 2, y: cyInstance.height() / 2 },
          duration: 200
        });
      }
    };
  }

  // Bind Reset 1:1 Scale
  const resetBtn = document.getElementById('btn-cy-reset');
  if (resetBtn) {
    resetBtn.onclick = () => {
      if (cyInstance) {
        cyInstance.animate({
          zoom: 1.0,
          center: { eles: cyInstance.elements() },
          duration: 300
        });
      }
    };
  }

  // Attach click listener for node drill-down
  cyInstance.on('tap', 'node', function(evt) {
    const node = evt.target;
    if (onNodeClickCallback) {
      onNodeClickCallback(node.data('raw'));
    }
  });

  return cyInstance;
}

/**
 * Re-centers and fits all process stages with smooth animation
 */
export function fitProcessGraph(animated = true) {
  if (!cyInstance) return;
  cyInstance.resize();
  
  if (animated) {
    cyInstance.animate({
      fit: { eles: cyInstance.elements(), padding: 35 },
      duration: 350,
      easing: 'ease-out-cubic'
    });
  } else {
    cyInstance.fit(undefined, 35);
  }
}
