"use strict";

const escapeHtml = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[ch]);

const formatTime = (iso) => {
  const date = new Date(iso);
  return date.toLocaleString("en-GB", {
    day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  });
};

class ApiClient {
  async request(method, url, body) {
    const response = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);
    return data;
  }

  timeline() { return this.request("GET", "/api/timeline"); }
  move(action) { return this.request("POST", `/api/cursor/${action}`); }
  jump(id) { return this.request("POST", `/api/cursor/jump/${encodeURIComponent(id)}`); }
  addEvent(payload) { return this.request("POST", "/api/events", payload); }
  deleteEvent(id) { return this.request("DELETE", `/api/events/${encodeURIComponent(id)}`); }
  moveEvent(id, beforeId) { return this.request("POST", `/api/events/${encodeURIComponent(id)}/move`, { before_id: beforeId }); }
  traceBackward() { return this.request("GET", "/api/trace/backward"); }
  traceForward() { return this.request("GET", "/api/trace/forward"); }
  clear() { return this.request("POST", "/api/clear"); }
}

class Toast {
  constructor(element) { this.el = element; this.timer = null; }

  show(message, kind = "success") {
    this.el.textContent = message;
    this.el.className = `toast show ${kind}`;
    clearTimeout(this.timer);
    this.timer = setTimeout(() => (this.el.className = "toast"), 2800);
  }
}

class StatsView {
  constructor(element) { this.el = element; }

  render(snapshot) {
    this.el.innerHTML = snapshot.phases.map((phase) => `
      <div class="stat" style="--c:${phase.color}">
        <span class="tactic">${phase.tactic}</span>
        <div class="count">${snapshot.stats[phase.name] || 0}</div>
        <div class="label">${escapeHtml(phase.label)}</div>
      </div>`).join("");
  }
}

class TraversalView {
  constructor(element) { this.el = element; }

  render(snapshot) {
    if (snapshot.is_empty) {
      this.el.innerHTML = `<div class="row"><span class="label">is_empty()</span><span class="chip">True</span></div>`;
      return;
    }
    const forward = snapshot.events.map((e) => `<span class="chip">${e.id}</span>`).join("→");
    const backward = snapshot.backward.map((id) => `<span class="chip">${id}</span>`).join("→");
    this.el.innerHTML = `
      <div class="row forward"><span class="label">for event in timeline (__iter__)</span>${forward}</div>
      <div class="row backward"><span class="label">reversed(timeline) (__reversed__)</span>${backward}</div>`;
  }
}

/*
 * Draws the chain from the real pointers (next_id / prev_id), so a broken
 * link would show up in red. Supports drag & drop to relink a node, and
 * animates the change: cards slide to their new place (FLIP) and every
 * link that did not exist before is redrawn.
 */
class TimelineView {
  constructor(element, handlers) {
    this.el = element;
    this.handlers = handlers; // { onSelect, onMove }
    this.trace = null;        // { direction, path: [...ids], patientZero }
    this.events = [];
    this.previousLinks = null;
    this.highlightId = null;
    this.dragId = null;
    this.dropBeforeId = undefined;
    this.bindDragAndDrop();
  }

  setTrace(trace) { this.trace = trace; }

  render(snapshot) {
    const oldPositions = this.nodePositions();
    const { events, cursor } = snapshot;
    this.events = events;

    if (!events.length) {
      this.el.innerHTML = `<div class="empty">The list is empty (first_event = last_event = None).<br>Add the first piece of evidence with the form below.</div>`;
      this.previousLinks = new Set();
      return;
    }

    const traced = new Set(this.trace ? this.trace.path : []);
    const parts = [`<div class="null-ref">None</div>`, this.link(null, events[0], traced)];

    events.forEach((event, index) => {
      const classes = ["node"];
      if (event.id === cursor) classes.push("cursor");
      if (traced.has(event.id)) classes.push(`traced-${this.trace.direction}`);
      if (this.trace?.patientZero === event.id) classes.push("patient-zero");
      if (event.id === this.highlightId) classes.push("just-moved");

      parts.push(`
        <article class="${classes.join(" ")}" data-id="${event.id}" draggable="true" style="--c:${event.phase.color}">
          <div class="ptr"><span><span class="grip">⠿</span>${event.id}</span><span class="sev ${event.severity}">${event.severity}</span></div>
          <div class="phase">${escapeHtml(event.phase.label)}</div>
          <div class="time">${formatTime(event.timestamp)}</div>
          <div class="summary">${escapeHtml(event.summary)}</div>
          <div class="host">⌁ ${escapeHtml(event.host)}</div>
          ${event.out_of_order ? `<span class="ooo" title="previous_event happened later">⚠ out of chronological order</span>` : ""}
        </article>`);

      parts.push(this.link(event, events[index + 1] || null, traced));
    });

    parts.push(`<div class="null-ref">None</div>`);
    this.el.innerHTML = parts.join("");
    this.highlightId = null;

    this.el.querySelectorAll(".node").forEach((node) =>
      node.addEventListener("click", () => this.handlers.onSelect(node.dataset.id)));

    this.slideNodes(oldPositions);
    this.previousLinks = new Set([...this.el.querySelectorAll(".link")].map((l) => l.dataset.key));
    this.el.querySelector(".node.cursor")
      ?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
  }

  link(left, right, traced) {
    const key = `${left ? left.id : "None"}>${right ? right.id : "None"}`;
    const classes = ["link"];
    if (this.previousLinks && !this.previousLinks.has(key)) classes.push("rewired");
    if (left && right && traced.has(left.id) && traced.has(right.id)) classes.push(this.trace.direction);

    // left.next_event must be right, and right.previous_event must be left
    let arrows = "";
    let label = [];
    if (left) {
      const ok = left.next_id === (right ? right.id : null);
      arrows += `<path class="fwd ${ok ? "" : "broken"}" pathLength="1" d="M6 10 H50 M44 5 L51 10 L44 15"/>`;
      label.push(right ? "next" : "next=None");
    }
    if (right) {
      const ok = right.prev_id === (left ? left.id : null);
      arrows += `<path class="bwd ${ok ? "" : "broken"}" pathLength="1" d="M50 22 H6 M12 17 L5 22 L12 27"/>`;
      label.push(left ? "prev" : "prev=None");
    }

    return `
      <div class="${classes.join(" ")}" data-key="${key}" data-before="${right ? right.id : ""}">
        <svg viewBox="0 0 56 30" aria-hidden="true">${arrows}</svg>
        <span class="lbl">${label.join(" · ")}</span>
      </div>`;
  }

  nodePositions() {
    const positions = {};
    this.el.querySelectorAll(".node").forEach((node) => { positions[node.dataset.id] = node.offsetLeft; });
    return positions;
  }

  slideNodes(oldPositions) {
    const firstRender = this.previousLinks === null;
    this.el.querySelectorAll(".node").forEach((node) => {
      const oldLeft = oldPositions[node.dataset.id];
      if (oldLeft === undefined) {
        if (!firstRender) node.classList.add("entering");
        return;
      }
      const delta = oldLeft - node.offsetLeft;
      if (delta !== 0) {
        node.animate(
          [{ transform: `translateX(${delta}px)` }, { transform: "translateX(0)" }],
          { duration: 500, easing: "cubic-bezier(.2,.8,.2,1)" },
        );
      }
    });
  }

  bindDragAndDrop() {
    this.el.addEventListener("dragstart", (e) => {
      const node = e.target.closest(".node");
      if (!node) return;
      this.dragId = node.dataset.id;
      e.dataTransfer.effectAllowed = "move";
      e.dataTransfer.setData("text/plain", this.dragId);
      this.el.classList.add("drag-active");
      requestAnimationFrame(() => node.classList.add("dragging"));
    });

    this.el.addEventListener("dragover", (e) => {
      if (!this.dragId) return;
      e.preventDefault();
      this.autoScroll(e.clientX);
      this.showDropTarget(this.beforeIdAt(e.clientX));
    });

    this.el.addEventListener("drop", (e) => {
      e.preventDefault();
      const id = this.dragId;
      const beforeId = this.dropBeforeId;
      this.endDrag();
      if (id && beforeId !== undefined) {
        this.highlightId = id;
        this.handlers.onMove(id, beforeId);
      }
    });

    this.el.addEventListener("dragend", () => this.endDrag());
  }

  // id of the node the dragged one should be inserted before (null = end)
  beforeIdAt(x) {
    for (const node of this.el.querySelectorAll(".node")) {
      if (node.dataset.id === this.dragId) continue;
      const rect = node.getBoundingClientRect();
      if (x < rect.left + rect.width / 2) return node.dataset.id;
    }
    return null;
  }

  showDropTarget(beforeId) {
    const dragged = this.events.find((e) => e.id === this.dragId);
    const unchanged = dragged.next_id === beforeId;
    this.dropBeforeId = unchanged ? undefined : beforeId;

    this.el.querySelectorAll(".link.drop-target").forEach((l) => l.classList.remove("drop-target"));
    if (unchanged) return;
    this.el.querySelector(`.link[data-before="${beforeId === null ? "" : beforeId}"]`)
      ?.classList.add("drop-target");
  }

  autoScroll(x) {
    const rect = this.el.getBoundingClientRect();
    if (x < rect.left + 70) this.el.scrollLeft -= 16;
    else if (x > rect.right - 70) this.el.scrollLeft += 16;
  }

  endDrag() {
    this.el.classList.remove("drag-active");
    this.el.querySelectorAll(".dragging, .drop-target").forEach((n) => n.classList.remove("dragging", "drop-target"));
    this.dragId = null;
    this.dropBeforeId = undefined;
  }
}

class DetailView {
  constructor(detailEl, traceEl, handlers) {
    this.el = detailEl;
    this.traceEl = traceEl;
    this.handlers = handlers; // { onJump, onDelete, onMove }
  }

  render(snapshot) {
    const event = snapshot.events.find((e) => e.id === snapshot.cursor);
    if (!event) {
      this.el.innerHTML = `<p class="muted">No event selected (cursor = None). Add evidence to start the investigation.</p>`;
      return;
    }

    const indicators = Object.entries(event.indicators)
      .map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd>`).join("");

    this.el.innerHTML = `
      <div class="badges" style="--c:${event.phase.color}">
        <span class="badge">${escapeHtml(event.phase.label)}</span>
        <span class="badge">MITRE ${event.phase.tactic}</span>
        <span class="sev ${event.severity}">${event.severity}</span>
        <span class="muted mono small">${event.type}</span>
      </div>
      <h3>${escapeHtml(event.summary)}</h3>
      <p class="muted">${escapeHtml(event.description) || "No description."}</p>
      <dl class="kv">
        <dt>event_id</dt><dd>${event.id}</dd>
        <dt>timestamp</dt><dd>${event.timestamp}</dd>
        <dt>host</dt><dd>${escapeHtml(event.host)}</dd>
        ${indicators}
      </dl>
      <div class="pointers">
        ${this.pointer("previous_event", event.prev_id)}
        ${this.pointer("next_event", event.next_id)}
      </div>
      <div class="move-buttons">
        <button class="btn" id="btn-move-earlier" ${event.prev_id ? "" : "disabled"}>◀ Move earlier</button>
        <button class="btn" id="btn-move-later" ${event.next_id ? "" : "disabled"}>Move later ▶</button>
      </div>
      <button class="btn danger" id="btn-delete">✕ Remove event from timeline</button>`;

    this.el.querySelectorAll(".pointer[data-id]").forEach((el) =>
      el.addEventListener("click", () => this.handlers.onJump(el.dataset.id)));
    this.el.querySelector("#btn-delete")
      .addEventListener("click", () => this.handlers.onDelete(event.id));
    this.el.querySelector("#btn-move-earlier")
      .addEventListener("click", () => this.handlers.onMove(event.id, "earlier"));
    this.el.querySelector("#btn-move-later")
      .addEventListener("click", () => this.handlers.onMove(event.id, "later"));
  }

  pointer(label, id) {
    return id
      ? `<div class="pointer" data-id="${id}"><span>${label}</span>${id}</div>`
      : `<div class="pointer null"><span>${label}</span>None</div>`;
  }

  renderTrace(direction, result) {
    this.traceEl.className = `trace-result ${direction}`;
    if (direction === "back") {
      const pz = result.patient_zero;
      this.traceEl.innerHTML = `
        <h4>⇠ Backward trace (following <code>prev</code>)</h4>
        <p>Patient zero: <b>${pz ? escapeHtml(pz.host) : "unknown"}</b>
           ${pz ? `- ${escapeHtml(pz.summary)}` : ""}</p>
        <div class="chips">${result.path.map((id) => `<span class="chip">${id}</span>`).join("←")}</div>`;
    } else {
      this.traceEl.innerHTML = `
        <h4>Forward trace (following <code>next</code>) ⇢</h4>
        <p>Compromised hosts: <b>${result.compromised_hosts.length}</b> ·
           Exfiltrated: <b>${result.exfiltrated_mb.toLocaleString()} MB</b></p>
        <div class="chips">${result.compromised_hosts.map((h) => `<span class="chip">${escapeHtml(h)}</span>`).join("")}</div>`;
    }
  }

  clearTrace() { this.traceEl.className = "trace-result hidden"; }
}

class EvidenceForm {
  constructor(form, fieldsContainer, typeSelect, onSubmit) {
    this.form = form;
    this.fieldsEl = fieldsContainer;
    this.typeSelect = typeSelect;
    this.eventTypes = {};
    this.typeSelect.addEventListener("change", () => this.renderFields());
    this.form.addEventListener("submit", (e) => {
      e.preventDefault();
      onSubmit(this.payload());
    });
  }

  setTypes(eventTypes) {
    if (Object.keys(this.eventTypes).length) return;
    this.eventTypes = eventTypes;
    this.typeSelect.innerHTML = Object.keys(eventTypes)
      .map((key) => `<option value="${key}">${key.replace(/_/g, " ")}</option>`).join("");
    this.renderFields();
  }

  renderFields() {
    const fields = this.eventTypes[this.typeSelect.value] || [];
    this.fieldsEl.innerHTML = fields.map((field) => `
      <label>${field.replace(/_/g, " ")}
        <input name="${field}" required ${/size|ports/.test(field) ? 'type="number" min="0" step="any"' : ""}>
      </label>`).join("");
  }

  payload() { return Object.fromEntries(new FormData(this.form).entries()); }

  reset() {
    this.form.reset();
    this.renderFields();
  }
}

class App {
  constructor() {
    this.api = new ApiClient();
    this.toast = new Toast(document.getElementById("toast"));
    this.stats = new StatsView(document.getElementById("stats"));
    this.timeline = new TimelineView(document.getElementById("timeline"), {
      onSelect: (id) => this.run(() => this.api.jump(id)),
      onMove: (id, beforeId) => this.moveEvent(id, beforeId),
    });
    this.traversal = new TraversalView(document.getElementById("traversal"));
    this.detail = new DetailView(
      document.getElementById("detail"),
      document.getElementById("trace-result"),
      {
        onJump: (id) => this.run(() => this.api.jump(id)),
        onDelete: (id) => this.run(() => this.api.deleteEvent(id), `${id} removed from the chain`),
        onMove: (id, direction) => this.moveOneStep(id, direction),
      },
    );
    this.form = new EvidenceForm(
      document.getElementById("evidence-form"),
      document.getElementById("dynamic-fields"),
      document.getElementById("event-type"),
      (payload) => this.addEvidence(payload),
    );
    this.bindControls();
  }

  bindControls() {
    document.querySelectorAll("[data-move]").forEach((btn) =>
      btn.addEventListener("click", () => this.run(() => this.api.move(btn.dataset.move))));
    document.getElementById("btn-clear").addEventListener("click", () =>
      this.run(() => this.api.clear(), "Timeline cleared"));
    document.getElementById("btn-trace-back").addEventListener("click", () => this.trace("back"));
    document.getElementById("btn-trace-forward").addEventListener("click", () => this.trace("forward"));

    document.addEventListener("keydown", (e) => {
      if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
      if (e.shiftKey && (e.key === "ArrowLeft" || e.key === "ArrowRight")) {
        e.preventDefault();
        if (this.snapshot?.cursor) this.moveOneStep(this.snapshot.cursor, e.key === "ArrowLeft" ? "earlier" : "later");
        return;
      }
      const keys = { ArrowLeft: "prev", ArrowRight: "next", Home: "first", End: "last" };
      if (keys[e.key]) {
        e.preventDefault();
        this.run(() => this.api.move(keys[e.key]));
      }
    });
  }

  async load() { await this.run(() => this.api.timeline()); }

  async run(action, successMessage) {
    try {
      const snapshot = await action();
      this.timeline.setTrace(null);
      this.detail.clearTrace();
      this.render(snapshot.timeline || snapshot);
      if (successMessage) this.toast.show(successMessage);
    } catch (error) {
      this.handleError(error);
    }
  }

  async trace(direction) {
    try {
      const result = direction === "back" ? await this.api.traceBackward() : await this.api.traceForward();
      this.timeline.setTrace({
        direction,
        path: result.path,
        patientZero: result.patient_zero?.id,
      });
      this.timeline.render(this.snapshot);
      this.detail.renderTrace(direction, result);
    } catch (error) {
      this.handleError(error);
    }
  }

  async addEvidence(payload) {
    try {
      const data = await this.api.addEvent(payload);
      this.render(data.timeline);
      this.form.reset();
      this.toast.show(`${data.created.id} added with ${this.insertionMethod(data)}`);
    } catch (error) {
      this.handleError(error);
    }
  }

  async moveEvent(id, beforeId) {
    let how = `insert_event_before(${beforeId})`;
    if (beforeId === null) how = "append_event";
    else if (this.snapshot.events[0].id === beforeId) how += " → prepend_event";
    this.timeline.highlightId = id;
    await this.run(() => this.api.moveEvent(id, beforeId), `${id} relinked: remove_event → ${how}`);
  }

  moveOneStep(id, direction) {
    const event = this.snapshot.events.find((e) => e.id === id);
    if (direction === "earlier") {
      if (event.prev_id) this.moveEvent(id, event.prev_id);
    } else if (event.next_id) {
      const next = this.snapshot.events.find((e) => e.id === event.next_id);
      this.moveEvent(id, next.next_id);
    }
  }

  insertionMethod(data) {
    const event = data.timeline.events.find((e) => e.id === data.created.id);
    if (!event.next_id) return "append_event";
    if (!event.prev_id) return "insert_event_before → prepend_event";
    return `insert_event_before(${event.next_id})`;
  }

  render(snapshot) {
    this.snapshot = snapshot;
    document.getElementById("case-title").textContent = snapshot.title;
    document.getElementById("node-count").textContent = snapshot.size;
    this.stats.render(snapshot);
    this.timeline.render(snapshot);
    this.traversal.render(snapshot);
    this.detail.render(snapshot);
    this.form.setTypes(snapshot.event_types);
  }

  handleError(error) {
    this.toast.show(error.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => new App().load());
