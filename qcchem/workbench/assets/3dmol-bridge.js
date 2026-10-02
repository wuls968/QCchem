(function () {
  const VIEWER_SELECTOR = ".qcchem-molecule-viewer";
  const CANVAS_SELECTOR = ".qcchem-molecule-viewer__canvas";
  const BRIDGE_FLAG = "qcchemBridgeHydrated";
  const PAYLOAD_HASH_KEY = "qcchemPayloadHash";
  const MOL_SCRIPT_ID = "qcchem-3dmol-script";
  const bridgeScript = document.currentScript;
  const MOL_SCRIPT_SRC = bridgeScript && bridgeScript.src
    ? new URL("3Dmol-2.5.5.min.js", bridgeScript.src).href
    : "/assets/3Dmol-2.5.5.min.js";
  let scriptPromise = null;
  const viewers = new Map();
  let scheduled = false;

  function payloadToXYZ(payload) {
    if (!payload.atoms || !Array.isArray(payload.atoms)) {
      return null;
    }
    const lines = [String(payload.atoms.length), payload.name || payload.title || "QCchem molecule"];
    payload.atoms.forEach((atom) => {
      lines.push([atom.elem || atom.element || "X", atom.x || 0, atom.y || 0, atom.z || 0].join(" "));
    });
    return lines.join("\n");
  }

  function ensureScript() {
    if (window.$3Dmol && typeof window.$3Dmol.createViewer === "function") {
      return Promise.resolve();
    }
    const existing = document.getElementById(MOL_SCRIPT_ID);
    if (existing && (existing.dataset.qcchem3dmolReady === "true" || (window.$3Dmol && typeof window.$3Dmol.createViewer === "function"))) {
      existing.dataset.qcchem3dmolReady = "true";
      return Promise.resolve();
    }
    if (existing && existing.dataset.qcchem3dmolReady === "true") {
      return Promise.resolve();
    }
    if (scriptPromise) {
      return scriptPromise;
    }

    scriptPromise = new Promise((resolve, reject) => {
      const script = existing || document.createElement("script");
      script.id = MOL_SCRIPT_ID;
      if (!existing) {
        script.src = MOL_SCRIPT_SRC;
        script.async = true;
      }
      script.onload = () => {
        script.dataset.qcchem3dmolReady = "true";
        scriptPromise = null;
        resolve();
      };
      script.onerror = () => {
        scriptPromise = null;
        reject(new Error("Unable to load 3Dmol bridge dependency."));
      };
      if (!existing) {
        document.head.appendChild(script);
      }
    });
    return scriptPromise;
  }

  function hydrateViewer(mountNode) {
    if (!mountNode) {
      return;
    }

    const moleculeJson = mountNode.getAttribute("data-molecule-json");
    if (!moleculeJson) {
      return;
    }
    if (mountNode.dataset[BRIDGE_FLAG] === "true" && mountNode.dataset.qcchemPayloadHash === moleculeJson) {
      return;
    }

    let payload;
    try {
      payload = JSON.parse(moleculeJson);
    } catch (_error) {
      mountNode.dataset[BRIDGE_FLAG] = "invalid";
      renderUnavailableState(mountNode.querySelector(CANVAS_SELECTOR) || mountNode);
      return;
    }

    const bridgeApi = window.$3Dmol;
    const renderNode = mountNode.querySelector(CANVAS_SELECTOR) || mountNode;
    if (!bridgeApi || typeof bridgeApi.createViewer !== "function") {
      mountNode.dataset[BRIDGE_FLAG] = "unavailable";
      renderUnavailableState(renderNode);
      return;
    }

    renderNode.replaceChildren();
    const previous = viewers.get(mountNode);
    if (previous) {
      previous.observer.disconnect();
      if (typeof previous.viewer.clear === "function") previous.viewer.clear();
    }
    const viewer = bridgeApi.createViewer(renderNode, { backgroundColor: "rgba(15, 28, 43, 0.94)" });
    if (payload.coordinates) {
      viewer.addModel(payload.coordinates, payload.format || "xyz");
    } else if (payload.atoms) {
      const xyz = payloadToXYZ(payload);
      if (xyz) {
        viewer.addModel(xyz, payload.format || "xyz");
      }
    } else if (payload.models) {
      payload.models.forEach((model) => viewer.addModel(model.coordinates, model.format || payload.format || "xyz"));
    }
    if (payload.style) {
      viewer.setStyle({}, payload.style);
    } else {
      viewer.setStyle({}, { stick: { radius: 0.15 }, sphere: { scale: 0.25 } });
    }
    (payload.labels || []).forEach((label) => {
      viewer.addLabel(label.text, {
        position: label.position,
        backgroundColor: "rgba(255, 250, 243, 0.86)",
        fontColor: "#20334a",
      });
    });
    viewer.zoomTo();
    const atoms = typeof viewer.selectedAtoms === "function" ? viewer.selectedAtoms({}) : (payload.atoms || []);
    if (typeof viewer.selectedAtoms === "function" && !atoms.length) {
      throw new Error("The molecule contains no readable atoms.");
    }
    mountNode.dataset.qcchemRenderedAtomCount = String(atoms.length);
    if (atoms.length > 1) {
      const spans = ["x", "y", "z"].map((axis) => {
        const positions = atoms.map((atom) => atom[axis]);
        return Math.max(...positions) - Math.min(...positions);
      });
      // Linear molecules on the view axis otherwise hide behind their front atom.
      if (spans[0] + spans[1] < 1e-7 && spans[2] > 1e-7 && typeof viewer.rotate === "function") {
        viewer.rotate(90, "y");
      }
      if (Math.max(...spans) < 3 && typeof viewer.zoom === "function") viewer.zoom(2);
    }
    viewer.render();
    const observer = typeof ResizeObserver === "function" ? new ResizeObserver(() => {
      if (mountNode.isConnected) {
        viewer.resize();
        viewer.render();
      }
    }) : { observe() {}, disconnect() {} };
    observer.observe(renderNode);
    viewers.set(mountNode, { viewer, observer });
    mountNode.dataset.qcchemPayloadHash = moleculeJson;
    mountNode.dataset[BRIDGE_FLAG] = "true";
  }

  function renderUnavailableState(target) {
    if (target) {
      target.textContent = "3Dmol viewer unavailable";
    }
  }

  function hydrate(id) {
    const target = id ? document.getElementById(id) : null;
    return ensureScript()
      .then(() => {
        if (!target) {
          return false;
        }
        hydrateViewer(target);
        return target.dataset[BRIDGE_FLAG] === "true";
      })
      .catch(() => {
        if (target) {
          renderUnavailableState(target.querySelector(CANVAS_SELECTOR) || target);
        }
        return false;
      });
  }

  function hydrateAll() {
    ensureScript()
      .then(() => {
        document.querySelectorAll(VIEWER_SELECTOR).forEach((mountNode) => {
          try {
            hydrateViewer(mountNode);
          } catch (error) {
            mountNode.dataset[BRIDGE_FLAG] = "error";
            renderUnavailableState(mountNode.querySelector(CANVAS_SELECTOR) || mountNode);
            console.error("QCchem molecular rendering failed", error);
          }
        });
      })
      .catch(() => {
        document.querySelectorAll(VIEWER_SELECTOR).forEach((mountNode) => {
          renderUnavailableState(mountNode.querySelector(CANVAS_SELECTOR) || mountNode);
        });
      });
  }

  window.QCChem3DMol = {
    hydrate(id) {
      return hydrate(id);
    },
    hydrateAll() {
      hydrateAll();
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", hydrateAll);
  } else {
    hydrateAll();
  }

  document.addEventListener("DOMContentLoaded", hydrateAll);
  document.addEventListener("dashrendered", hydrateAll);
  if (typeof MutationObserver === "function") {
    const mounts = new MutationObserver((records) => {
    const relevant = records.some((record) =>
      record.type === "attributes" || Array.from(record.addedNodes).some((node) =>
        node.nodeType === 1 && (node.matches(VIEWER_SELECTOR) || node.querySelector(VIEWER_SELECTOR)))
    );
    viewers.forEach((entry, node) => {
      if (!node.isConnected) {
        entry.observer.disconnect();
        if (typeof entry.viewer.clear === "function") entry.viewer.clear();
        viewers.delete(node);
      }
    });
    if (relevant && !scheduled) {
      scheduled = true;
      requestAnimationFrame(() => { scheduled = false; hydrateAll(); });
    }
  });
  mounts.observe(document.documentElement, {
    childList: true, subtree: true, attributes: true, attributeFilter: ["data-molecule-json"],
  });
  }
})();
