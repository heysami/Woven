DS.behavior("filter-chip", {
  on: {
    "click": function (e, root) {
      var open = root.classList.toggle("is-open");
      root.setAttribute("aria-expanded", open ? "true" : "false");
      DS.emit(root, "ds:change", { open: open });
    }
  },
  init: function (root) { root.setAttribute("data-ds-inited", "1"); }
});
