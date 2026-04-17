(function () {
  const VIEWER_SELECTOR = ".qcchem-molecule-viewer";
  const CANVAS_SELECTOR = ".qcchem-molecule-viewer__canvas";
  const BRIDGE_FLAG = "qcchemBridgeHydrated";
  const MOL_SCRIPT_ID = "qcchem-3dmol-script";
  const MOL_SCRIPT_SRC = "https://3Dmol.org/build/3Dmol-min.js";

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
    const existing = document.getElementById(MOL_SCRIPT_ID);
    if (existing) {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.id = MOL_SCRIPT_ID;
      script.src = MOL_SCRIPT_SRC;
      script.async = true;
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Unable to load 3Dmol bridge dependency."));
      document.head.appendChild(script);
    });
  }

  function hydrateViewer(mountNode) {
    if (!mountNode || mountNode.dataset[BRIDGE_FLAG] === "true") {
      return;
    }

    const moleculeJson = mountNode.getAttribute("data-molecule-json");
    if (!moleculeJson) {
      return;
    }

    let payload;
    try {
      payload = JSON.parse(moleculeJson);
    } catch (_error) {
      element.dataset[BRIDGE_FLAG] = "invalid";
      return;
    }

    const bridgeApi = window.$3Dmol;
    if (!bridgeApi || typeof bridgeApi.createViewer !== "function") {
      return;
    }

    const renderNode = mountNode.querySelector(CANVAS_SELECTOR) || mountNode;
    const viewer = bridgeApi.createViewer(renderNode, { backgroundColor: "rgba(15, 28, 43, 0.94)" });
    if (payload.coordinates) {
      viewer.addModel(payload.coordinates, payload.format || "xyz");
    } else if (payload.atoms) {
      const atomModel = viewer.addModel();
      if (atomModel && typeof atomModel.addAtoms === "function") {
        atomModel.addAtoms(payload.atoms);
      } else {
        const xyz = payloadToXYZ(payload);
        if (xyz) {
          viewer.addModel(xyz, payload.format || "xyz");
        }
      }
    } else if (payload.models) {
      payload.models.forEach((model) => viewer.addModel(model.coordinates, model.format || payload.format || "xyz"));
    }
    if (payload.style) {
      viewer.setStyle({}, payload.style);
    } else {
      viewer.setStyle({}, { stick: {} });
    }
    (payload.labels || []).forEach((label) => {
      viewer.addLabel(label.text, {
        position: label.position,
        backgroundColor: "rgba(255, 250, 243, 0.86)",
        fontColor: "#20334a",
      });
    });
    viewer.zoomTo();
    viewer.render();
    mountNode.dataset[BRIDGE_FLAG] = "true";
  }

  function renderUnavailableState(target) {
    if (target && !target.textContent) {
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
          renderUnavailableState(target);
        }
        return false;
      });
  }

  function hydrateAll() {
    ensureScript()
      .then(() => {
        document.querySelectorAll(VIEWER_SELECTOR).forEach(hydrateViewer);
      })
      .catch(() => {
        document.querySelectorAll(VIEWER_SELECTOR).forEach(renderUnavailableState);
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
})();
