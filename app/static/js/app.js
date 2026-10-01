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

class TimelineView {
  constructor(element, onSelect) {
    this.el = element;
    this.onSelect = onSelect;
    this.trace = null; // { direction, path: [...ids], patientZero }
  }

  setTrace(trace) { this.trace = trace; }

  render(snapshot) {
    const { events, cursor } = snapshot;
    if (!events.length) {
      this.el.innerHTML = `<div class="empty">The list is empty (first_event = last_event = None).<br>Add the first piece of evidence with the form below.</div>`;
      return;
    }

    const traced = new Set(this.trace ? this.trace.path : []);
    const linkClass = this.trace ? this.trace.direction : "";
    const parts = [`<div class="null-ref">None ← first_event</div>`, this.link("")];

    events.forEach((event, index) => {
      const classes = ["node"];
      if (event.id === cursor) classes.push("cursor");
      if (traced.has(event.id)) classes.push(`traced-${this.trace.direction}`);
      if (this.trace?.patientZero === event.id) classes.push("patient-zero");

      parts.push(`
        <article class="${classes.join(" ")}" data-id="${event.id}" style="--c:${event.phase.color}">
          <div class="ptr"><span>${event.id}</span><span class="sev ${event.severity}">${event.severity}</span></div>
          <div class="phase">${escapeHtml(event.phase.label)}</div>
          <div class="time">${formatTime(event.timestamp)}</div>
          <div class="summary">${escapeHtml(event.summary)}</div>
          <div class="host">⌁ ${escapeHtml(event.host)}</div>
        </article>`);

      const bothTraced = traced.has(event.id) && traced.has(events[index + 1]?.id);
      if (index < events.length - 1) parts.push(this.link(bothTraced ? linkClass : ""));
    });

    parts.push(this.link(""), `<div class="null-ref">last_event → None</div>`);
    this.el.innerHTML = parts.join("");

    this.el.querySelectorAll(".node").forEach((node) =>
      node.addEventListener("click", () => this.onSelect(node.dataset.id)));
    this.el.querySelector(".node.cursor")
      ?.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
  }

  link(kind) {
    return `<div class="link ${kind}"><span>next</span><span class="arrow">⇄</span><span>prev</span></div>`;
  }
}

class DetailView {
  constructor(detailEl, traceEl, handlers) {
    this.el = detailEl;
    this.traceEl = traceEl;
    this.handlers = handlers; // { onJump, onDelete }
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
      <button class="btn danger" id="btn-delete">✕ Remove event from timeline</button>`;

    this.el.querySelectorAll(".pointer[data-id]").forEach((el) =>
      el.addEventListener("click", () => this.handlers.onJump(el.dataset.id)));
    this.el.querySelector("#btn-delete")
      .addEventListener("click", () => this.handlers.onDelete(event.id));
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
    this.timeline = new TimelineView(document.getElementById("timeline"), (id) => this.run(() => this.api.jump(id)));
    this.detail = new DetailView(
      document.getElementById("detail"),
      document.getElementById("trace-result"),
      {
        onJump: (id) => this.run(() => this.api.jump(id)),
        onDelete: (id) => this.run(() => this.api.deleteEvent(id), `${id} removed from the chain`),
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
      this.toast.show(`${data.created.id} inserted in chronological order`);
    } catch (error) {
      this.handleError(error);
    }
  }

  render(snapshot) {
    this.snapshot = snapshot;
    document.getElementById("case-title").textContent = snapshot.title;
    document.getElementById("node-count").textContent = snapshot.size;
    this.stats.render(snapshot);
    this.timeline.render(snapshot);
    this.detail.render(snapshot);
    this.form.setTypes(snapshot.event_types);
  }

  handleError(error) {
    this.toast.show(error.message, "error");
  }
}

document.addEventListener("DOMContentLoaded", () => new App().load());
