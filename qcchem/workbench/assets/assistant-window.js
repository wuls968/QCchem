document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("qcchem-ai-assistant-window");
  const dragHandle = document.getElementById("qcchem-ai-assistant-drag-handle");
  const resizeHandle = document.getElementById("qcchem-ai-assistant-resize-handle");
  const body = document.getElementById("qcchem-ai-assistant-body");
  const providerDrawer = document.getElementById("qcchem-ai-provider-drawer");

  if (!root || !dragHandle || !resizeHandle || !body || !providerDrawer) {
    return;
  }

  const STORAGE_KEY = "qcchem.ai.assistantWindow.v1";
  const EDGE_MARGIN = 12;
  const MIN_WIDTH = 320;
  const MIN_HEIGHT = 280;
  const MAX_WIDTH_PADDING = 24;
  const MAX_HEIGHT_PADDING = 24;

  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);

  const measureDefaultState = () => {
    const width = Math.min(440, window.innerWidth - 48);
    const height = Math.min(620, window.innerHeight - 64);
    return {
      width,
      height,
      left: Math.max(EDGE_MARGIN, window.innerWidth - width - 28),
      top: Math.max(24, window.innerHeight - height - 28),
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

  const applyState = (state) => {
    const maxWidth = Math.max(MIN_WIDTH, window.innerWidth - MAX_WIDTH_PADDING);
    const maxHeight = Math.max(MIN_HEIGHT, window.innerHeight - MAX_HEIGHT_PADDING);
    const width = clamp(state.width, MIN_WIDTH, maxWidth);
    const height = clamp(state.height, MIN_HEIGHT, maxHeight);
    const left = clamp(state.left, EDGE_MARGIN, window.innerWidth - width - EDGE_MARGIN);
    const top = clamp(state.top, EDGE_MARGIN, window.innerHeight - height - EDGE_MARGIN);

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

  let shellState = applyState(readPersistedState() || measureDefaultState());
  let expandedHeight = shellState.height;

  const beginPointerInteraction = ({
    event,
    cursor,
    onMove,
  }) => {
    event.preventDefault();
    const startX = event.clientX;
    const startY = event.clientY;
    document.body.style.cursor = cursor;
    root.style.transition = "none";

    const move = (moveEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaY = moveEvent.clientY - startY;
      shellState = applyState(onMove(shellState, deltaX, deltaY));
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
      onMove: (state, deltaX, deltaY) => ({
        ...state,
        left: state.left + deltaX,
        top: state.top + deltaY,
      }),
    });
  });

  resizeHandle.addEventListener("pointerdown", (event) => {
    beginPointerInteraction({
      event,
      cursor: "nwse-resize",
      onMove: (state, deltaX, deltaY) => ({
        ...state,
        width: state.width + deltaX,
        height: state.height + deltaY,
      }),
    });
  });

  window.addEventListener("resize", () => {
    shellState = applyState(shellState);
  });

  const syncMinimizedState = () => {
    const bodyHidden = body.hasAttribute("hidden");
    const drawerHidden = providerDrawer.hasAttribute("hidden");
    if (bodyHidden) {
      expandedHeight = shellState.height;
      const compactHeight = dragHandle.offsetHeight + resizeHandle.offsetHeight + (drawerHidden ? 18 : providerDrawer.offsetHeight + 24);
      shellState = applyState({
        ...shellState,
        height: compactHeight,
      });
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

  const observer = new MutationObserver(() => {
    syncMinimizedState();
  });
  observer.observe(body, { attributes: true, attributeFilter: ["hidden"] });
  observer.observe(providerDrawer, { attributes: true, attributeFilter: ["hidden"] });
  syncMinimizedState();
});
