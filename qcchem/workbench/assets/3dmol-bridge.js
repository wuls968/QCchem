(function () {
  const VIEWER_SELECTOR = ".qcchem-molecule-viewer";
  const BRIDGE_FLAG = "qcchemBridgeHydrated";
  const MOL_SCRIPT_ID = "qcchem-3dmol-script";
  const MOL_SCRIPT_SRC = "https://3Dmol.org/build/3Dmol-min.js";

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

  function hydrateViewer(element) {
    if (!element || element.dataset[BRIDGE_FLAG] === "true") {
      return;
    }

    const moleculeJson = element.getAttribute("data-molecule-json");
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

    const viewer = bridgeApi.createViewer(element, { backgroundColor: "rgba(15, 28, 43, 0.94)" });
    if (payload.coordinates) {
      viewer.addModel(payload.coordinates, payload.format || "xyz");
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
    element.dataset[BRIDGE_FLAG] = "true";
  }

  function hydrateAllViewers() {
    ensureScript()
      .then(() => {
        document.querySelectorAll(VIEWER_SELECTOR).forEach(hydrateViewer);
      })
      .catch(() => {
        document.querySelectorAll(VIEWER_SELECTOR).forEach((element) => {
          if (!element.textContent) {
            element.textContent = "3Dmol viewer unavailable";
          }
        });
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", hydrateAllViewers);
  } else {
    hydrateAllViewers();
  }

  document.addEventListener("DOMContentLoaded", hydrateAllViewers);
  document.addEventListener("dashrendered", hydrateAllViewers);
})();
