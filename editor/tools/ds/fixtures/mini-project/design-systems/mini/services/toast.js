// @desc Toast messages. DS.toast.show(message, {variant}) -> the toast element.
DS.service("toast", function (DS) {
  return {
    show: function (message, opts) {
      var host = document.body;
      var t = document.createElement("div");
      t.className = "toast-msg";
      t.setAttribute("role", "status");
      t.textContent = message;
      host.appendChild(t);
      return t;
    }
  };
});
