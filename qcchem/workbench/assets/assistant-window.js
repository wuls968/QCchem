(() => {
  const STORAGE_KEY = "qcchem.ai.assistantWindow.v1";
  const EDGE_MARGIN = 12;
  const MIN_WIDTH = 320;
  const MIN_HEIGHT = 280;
  const COMPACT_MIN_HEIGHT = 72;
  const MAX_WIDTH_PADDING = 24;
  const SAFE_TOP = 84;

  let initialized = false;
  let shellState = null;
  let expandedHeight = null;

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  const safeViewportTop = () => Math.max(SAFE_TOP, (window.visualViewport?.offsetTop || 0) + 56);

  const minWindowWidth = () => Math.min(MIN_WIDTH, Math.max(260, window.innerWidth - EDGE_MARGIN * 2));

  const measureDefaultState = () => {
    const width = Math.min(440, window.innerWidth - 48);
    const top = safeViewportTop();
    const height = Math.min(620, Math.max(MIN_HEIGHT, window.innerHeight - top - 24));
    return {
      width,
      height,
      left: Math.max(EDGE_MARGIN, window.innerWidth - width - 28),
      top: Math.max(top, window.innerHeight - height - 28),
    };
  };

  const readPersistedState = () => {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return null;
      }
      const parsed = JSON.parse(raw);
      if (
        typeof parsed.left !== "number" ||
        typeof parsed.top !== "number" ||
        typeof parsed.width !== "number" ||
        typeof parsed.height !== "number"
      ) {
        return null;
      }
      return parsed;
    } catch (_error) {
      return null;
    }
  };

  const persistState = (state) => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  };

  const boot = () => {
    if (initialized) {
      return true;
    }

    const root = document.getElementById("qcchem-ai-assistant-window");
    const dragHandle = document.getElementById("qcchem-ai-assistant-drag-handle");
    const resizeHandle = document.getElementById("qcchem-ai-assistant-resize-handle");
    const resetButton = document.getElementById("qcchem-ai-assistant-reset-position");
    const body = document.getElementById("qcchem-ai-assistant-body");
    const providerDrawer = document.getElementById("qcchem-ai-provider-drawer");

    if (!root || !dragHandle || !resizeHandle || !body || !providerDrawer) {
      return false;
    }

    const applyState = (state, options = {}) => {
      const minHeight = options.allowCompactHeight ? COMPACT_MIN_HEIGHT : MIN_HEIGHT;
      const minTop = safeViewportTop();
      const minWidth = minWindowWidth();
      const maxWidth = Math.max(minWidth, window.innerWidth - MAX_WIDTH_PADDING);
      const maxHeight = Math.max(minHeight, window.innerHeight - minTop - EDGE_MARGIN);
      const width = clamp(state.width, minWidth, maxWidth);
      const height = clamp(state.height, minHeight, maxHeight);
      const maxLeft = Math.max(EDGE_MARGIN, window.innerWidth - width - EDGE_MARGIN);
      const maxTop = Math.max(minTop, window.innerHeight - height - EDGE_MARGIN);
      const left = clamp(state.left, EDGE_MARGIN, maxLeft);
      const top = clamp(state.top, minTop, maxTop);

      const nextState = { left, top, width, height };
      root.style.left = `${left}px`;
      root.style.top = `${top}px`;
      root.style.width = `${width}px`;
      root.style.height = `${height}px`;
      root.style.right = "auto";
      root.style.bottom = "auto";
      persistState(nextState);
      return nextState;
    };

    shellState = applyState(readPersistedState() || measureDefaultState());
    expandedHeight = shellState.height;

    const compactWindowHeight = () =>
      dragHandle.offsetHeight + resizeHandle.offsetHeight + (providerDrawer.hasAttribute("hidden") ? 18 : providerDrawer.offsetHeight + 24);

    const resetToDefaultState = () => {
      shellState = applyState(measureDefaultState());
      expandedHeight = shellState.height;
      if (body.hasAttribute("hidden")) {
        shellState = applyState(
          {
            ...shellState,
            height: compactWindowHeight(),
          },
          { allowCompactHeight: true },
        );
        root.dataset.minimized = "true";
        return;
      }
      root.dataset.minimized = "false";
    };

    const beginPointerInteraction = ({ event, cursor, onMove }) => {
      event.preventDefault();
      const startX = event.clientX;
      const startY = event.clientY;
      const origin = { ...shellState };
      document.body.style.cursor = cursor;
      root.style.transition = "none";

      const move = (moveEvent) => {
        const deltaX = moveEvent.clientX - startX;
        const deltaY = moveEvent.clientY - startY;
        shellState = applyState(onMove(origin, deltaX, deltaY));
      };

      const end = () => {
        document.body.style.cursor = "";
        root.style.transition = "";
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerup", end);
      };

      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", end);
    };

    dragHandle.addEventListener("pointerdown", (event) => {
      beginPointerInteraction({
        event,
        cursor: "grabbing",
        onMove: (origin, deltaX, deltaY) => ({
          ...origin,
          left: origin.left + deltaX,
          top: origin.top + deltaY,
        }),
      });
    });

    dragHandle.addEventListener("dblclick", (event) => {
      event.preventDefault();
      resetToDefaultState();
    });

    if (resetButton) {
      resetButton.addEventListener("click", (event) => {
        event.preventDefault();
        resetToDefaultState();
      });
    }

    resizeHandle.addEventListener("pointerdown", (event) => {
      beginPointerInteraction({
        event,
        cursor: "nwse-resize",
        onMove: (origin, deltaX, deltaY) => ({
          ...origin,
          width: origin.width + deltaX,
          height: origin.height + deltaY,
        }),
      });
    });

    const syncMinimizedState = () => {
      const bodyHidden = body.hasAttribute("hidden");
      if (bodyHidden) {
        expandedHeight = Math.max(expandedHeight || 0, shellState.height);
        shellState = applyState({
          ...shellState,
          height: compactWindowHeight(),
        }, { allowCompactHeight: true });
        root.dataset.minimized = "true";
        return;
      }
      root.dataset.minimized = "false";
      if (shellState.height < expandedHeight) {
        shellState = applyState({
          ...shellState,
          height: expandedHeight,
        });
      }
    };

    const stateObserver = new MutationObserver(() => {
      syncMinimizedState();
    });
    stateObserver.observe(body, { attributes: true, attributeFilter: ["hidden"] });
    stateObserver.observe(providerDrawer, { attributes: true, attributeFilter: ["hidden"] });

    window.addEventListener("resize", () => {
      shellState = applyState(shellState);
    });

    syncMinimizedState();
    initialized = true;
    return true;
  };

  const mountObserver = new MutationObserver(() => {
    if (boot()) {
      mountObserver.disconnect();
    }
  });

  if (!boot()) {
    mountObserver.observe(document.body, { childList: true, subtree: true });
    window.requestAnimationFrame(() => {
      boot();
    });
  }
})();
