// Small UI helpers (no framework needed)
document.addEventListener("DOMContentLoaded", function () {
  // Mobile sidebar toggle
  var sidebar = document.getElementById("sidebar");
  var backdrop = document.getElementById("backdrop");
  var menuBtn = document.getElementById("menuBtn");
  function toggleMenu(open) {
    if (!sidebar) return;
    sidebar.classList.toggle("open", open);
    backdrop.classList.toggle("show", open);
  }
  if (menuBtn) menuBtn.addEventListener("click", function () { toggleMenu(!sidebar.classList.contains("open")); });
  if (backdrop) backdrop.addEventListener("click", function () { toggleMenu(false); });

  // Auto-hide success/info messages after 5 seconds
  document.querySelectorAll(".app-alert.alert-success, .app-alert.alert-info").forEach(function (el) {
    setTimeout(function () { el.style.transition = "opacity .5s"; el.style.opacity = "0";
      setTimeout(function () { el.remove(); }, 500); }, 5000);
  });

  // Confirm dialogs for destructive actions: <form data-confirm="Are you sure?">
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // Prediction form: client-side range check + prevent double submit
  var pf = document.getElementById("predictForm");
  if (pf) {
    pf.addEventListener("submit", function (e) {
      var bad = null;
      pf.querySelectorAll("input[type=number]").forEach(function (inp) {
        var v = parseFloat(inp.value), min = parseFloat(inp.min), max = parseFloat(inp.max);
        var invalid = inp.value === "" || isNaN(v) || v < min || v > max;
        inp.classList.toggle("is-invalid", invalid);
        if (invalid && !bad) bad = inp;
      });
      if (bad) { e.preventDefault(); bad.focus(); return; }
      var btn = document.getElementById("submitBtn");
      if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Predicting...'; }
    });
  }
});
