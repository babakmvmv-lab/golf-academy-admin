(function () {
  /* پنل اعضا به زیردامنهٔ اختصاصی منتقل شد (panel.puttclub.ir).
     نشانی http تا زمان صدور گواهی HTTPS زیردامنه است؛ پس از فعال‌شدن اجبار HTTPS،
     سرور خودکار به نسخهٔ امن ارتقا می‌دهد. */
  var PANEL = "http://panel.puttclub.ir";
  function isAcademyPath(href) {
    if (!href) return false;
    try {
      var u = new URL(href, location.origin);
      if (u.origin !== location.origin) return false;
      var p = u.pathname.replace(/\/+$/, "") || "/";
      return p === "/academy";
    } catch (e) {
      return href === "/academy" || href === "/academy/";
    }
  }
  function go(ev) {
    if (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      if (ev.stopImmediatePropagation) ev.stopImmediatePropagation();
    }
    location.href = PANEL;
  }
  document.addEventListener(
    "click",
    function (ev) {
      var a = ev.target && ev.target.closest && ev.target.closest("a");
      if (!a) return;
      if (a.id === "enter-members" || (a.classList && a.classList.contains("enter-members")) || isAcademyPath(a.getAttribute("href"))) {
        go(ev);
      }
    },
    true
  );
  if ((location.pathname.replace(/\/+$/, "") || "/") === "/academy") {
    location.replace(PANEL);
  }
})();
