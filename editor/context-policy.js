/* Pure prompt helpers, shared by the UI and regression checks. */
(function (root) {
  "use strict";
  function dedupeInputs(inputs) {
    const seen = new Map();
    return (Array.isArray(inputs) ? inputs : []).flatMap(input => {
      if (!input.sourceId) return [input];
      const { label, ...payload } = input;
      const key = JSON.stringify(payload);
      if (seen.has(key)) {
        const original = seen.get(key);
        if (label && !original.labels.includes(label)) original.labels.push(label);
        return [];
      }
      const copy = { ...input, labels: label ? [label] : [] };
      seen.set(key, copy);
      return [copy];
    }).map(input => input.labels ? { ...input, label: input.labels.join(" / ") } : input);
  }
  function handoffPrompt(summary, text) {
    return "[CONTINUING WORK]\nRetain the approved decisions and verified work below. "
      + "Apply the current thread's checks. Read referenced files when needed; "
      + "do not repeat completed work or answered gates.\n\n"
      + String(summary || "").trim() + "\n\n[CURRENT REQUEST]\n" + (text || "");
  }
  function handoffOptions(context, overrides = {}) {
    const c = context || {};
    const options = { branch: c.branch, prototype: c.prototype, tier: c.tier,
      guards: c.guards, model: c.model || (c.agent_id ? c.agent_id + "-default" : undefined),
      agentId: c.agent_id, ...overrides };
    if (options.prototype) options.branch = options.prototype;
    return options;
  }
  const api = { dedupeInputs, handoffPrompt, handoffOptions };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.WovenContext = api;
})(typeof window === "undefined" ? globalThis : window);
