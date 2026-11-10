"use strict";

// Authenticated native images are read by the host; browser images remain same-origin.
(() => {
  const isNative = () => typeof window.AURORA?.invoke === "function";
  function safeUrl(value) {
    if (typeof value !== "string" || !value) return null;
    try {
      const parsed = new URL(value, location.href);
      const local = isNative() && typeof window.AURORA.isLocal === 'function'
        ? window.AURORA.isLocal(parsed) : parsed.origin === location.origin;
      return local && parsed.pathname === "/api/account/avatar"
        ? parsed.pathname + parsed.search : null;
    } catch (_) { return null; }
  }
  function render(host, value) {
    const url = isNative() && typeof window.AURORA.imageURL !== 'function' ? null : safeUrl(value);
    host.dataset.avatarUrl = url || "";
    host.querySelector("[data-avatar-image]")?.remove();
    const initial = host.querySelector("[data-avatar-initial]");
    initial.hidden = false;
    if (!url) return;
    const image = new Image();
    image.alt = "";
    image.dataset.avatarImage = "";
    image.hidden = true;
    image.addEventListener("load", () => {
      if (!host.contains(image)) return;
      initial.hidden = true;
      image.hidden = false;
    });
    image.addEventListener("error", () => {
      if (!host.contains(image)) return;
      initial.hidden = false;
      image.remove();
    });
    host.append(image);
    if (isNative()) {
      window.AURORA.imageURL(url).then(source => {
        if (host.contains(image)) image.src = source;
      }).catch(() => {
        if (!host.contains(image)) return;
        initial.hidden = false;
        image.remove();
      });
    } else image.src = url;
  }
  function setUrl(value) {
    document.querySelectorAll("[data-account-avatar]").forEach(host => render(host, value));
  }
  window.AvatarDisplay = {setUrl, isNative, safeUrl};
  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-account-avatar]").forEach(host => render(host, host.dataset.avatarUrl));
  });
})();
