/* Aurora/Octavian wallpaper overlay injected at build time.
   WALLPAPERS and DEFAULT_WALLPAPER are substituted by the build script. */
(function () {
  var WALLPAPERS = __WALLPAPERS__;
  var DEFAULT_WALLPAPER = "__DEFAULT__";
  var KEY = "aurora.desktop.background";

  function apply(url) {
    var b = document.body;
    b.style.backgroundImage = 'url("' + url + '")';
    b.style.backgroundSize = "cover";
    b.style.backgroundPosition = "center center";
    b.style.backgroundRepeat = "no-repeat";
    b.style.backgroundAttachment = "fixed";
    try { localStorage.setItem(KEY, url); } catch (e) {}
    var nodes = document.querySelectorAll("[data-aurora-wp]");
    for (var i = 0; i < nodes.length; i++) {
      nodes[i].setAttribute("aria-pressed", String(nodes[i].getAttribute("data-aurora-wp") === url));
    }
  }

  function option(wp, close) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "wallpaper-option";
    b.setAttribute("data-aurora-wp", wp.url);
    b.style.cssText = "display:flex;align-items:center;gap:11px;width:100%;text-align:left;border:1px solid #ffffff33;border-radius:12px;background:#ffffff12;color:#fff;padding:8px;margin-top:7px;cursor:pointer;font:inherit;font-size:12px";
    var img = document.createElement("img");
    img.src = wp.url;
    img.alt = wp.name;
    img.style.cssText = "width:92px;height:54px;object-fit:cover;border-radius:8px";
    var label = document.createElement("span");
    label.textContent = wp.name;
    b.appendChild(img);
    b.appendChild(label);
    b.addEventListener("click", function () {
      apply(wp.url);
      if (close) { close.hidden = true; }
    });
    return b;
  }

  function buildFloating() {
    var wrap = document.createElement("div");
    wrap.id = "auroraWallpaperPanel";
    wrap.style.cssText = "position:fixed;z-index:2147483000;right:18px;bottom:86px;font:13px/1.4 system-ui,sans-serif";

    var panel = document.createElement("div");
    panel.id = "auroraWallpaperList";
    panel.hidden = true;
    panel.style.cssText = "width:min(380px,calc(100vw - 36px));max-height:70vh;overflow:auto;padding:14px;border:1px solid #ffffff3d;border-radius:18px;background:rgba(8,26,44,.94);backdrop-filter:blur(24px);box-shadow:0 22px 80px #0008;margin-bottom:10px;color:#eaf6ff";
    var head = document.createElement("div");
    head.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:6px";
    var h = document.createElement("strong");
    h.textContent = "Desktop backgrounds";
    var close = document.createElement("button");
    close.type = "button";
    close.textContent = "\u00d7";
    close.style.cssText = "border:1px solid #ffffff33;border-radius:8px;background:#ffffff12;color:#fff;font-size:18px;line-height:1;padding:2px 8px;cursor:pointer";
    close.addEventListener("click", function () { panel.hidden = true; });
    head.appendChild(h);
    head.appendChild(close);
    panel.appendChild(head);
    for (var i = 0; i < WALLPAPERS.length; i++) {
      panel.appendChild(option(WALLPAPERS[i], panel));
    }

    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.textContent = "\u25c9 Backgrounds";
    toggle.style.cssText = "float:right;border:1px solid #ffffff45;border-radius:11px;background:rgba(10,32,58,.85);color:#eaf6ff;font:inherit;font-size:12px;padding:8px 13px;cursor:pointer;backdrop-filter:blur(18px)";
    toggle.addEventListener("click", function () { panel.hidden = !panel.hidden; });

    wrap.appendChild(panel);
    wrap.appendChild(toggle);
    document.body.appendChild(wrap);
  }

  function init() {
    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) {}
    apply(saved || DEFAULT_WALLPAPER);

    var picker = document.getElementById("wallpaperPicker");
    if (picker) {
      var heading = picker.querySelector(".wallpaper-heading");
      var section = document.createElement("div");
      section.style.marginTop = "10px";
      var title = document.createElement("div");
      title.textContent = "SYSTEM ARTWORK";
      title.style.cssText = "font-size:10px;letter-spacing:.16em;opacity:.75;margin:6px 0 2px";
      section.appendChild(title);
      for (var i = 0; i < WALLPAPERS.length; i++) {
        section.appendChild(option(WALLPAPERS[i], picker));
      }
      if (heading && heading.nextSibling) {
        picker.insertBefore(section, heading.nextSibling);
      } else {
        picker.appendChild(section);
      }
    } else {
      buildFloating();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
