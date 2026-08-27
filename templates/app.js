// Keyboard navigation, vim-style.
//   index:  j/k or down/up move the selection, l/right/Enter opens it
//   post:   h/left goes back
(function () {
  "use strict";

  var index = Array.prototype.slice.call(
    document.querySelectorAll("article h2.post-title a")
  );
  var selected = -1;

  function articleFor(link) {
    return link.closest("article");
  }

  function highlight(i) {
    index.forEach(function (link) {
      articleFor(link).classList.remove("selected");
    });
    selected = Math.max(0, Math.min(i, index.length - 1));
    var article = articleFor(index[selected]);
    article.classList.add("selected");
    article.scrollIntoView({ block: "nearest" });
  }

  function goBack() {
    if (document.referrer) {
      history.back();
    } else {
      location.href = "/";
    }
  }

  document.addEventListener("keydown", function (e) {
    var t = e.target;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var k = e.key;

    if (index.length) {
      if (k === "j" || k === "ArrowDown") {
        e.preventDefault();
        highlight(selected < 0 ? 0 : selected + 1);
        return;
      }
      if (k === "k" || k === "ArrowUp") {
        e.preventDefault();
        highlight(selected < 0 ? index.length - 1 : selected - 1);
        return;
      }
      if (selected >= 0 && (k === "l" || k === "ArrowRight" || k === "Enter")) {
        e.preventDefault();
        location.href = index[selected].href;
        return;
      }
    } else if (k === "h" || k === "ArrowLeft") {
      e.preventDefault();
      goBack();
    }
  });

  function kbd(key) {
    return "<kbd>" + key + "</kbd>";
  }

  var hint = document.createElement("p");
  hint.className = "kbd-hint";
  if (index.length) {
    hint.innerHTML =
      kbd("j") + "/" + kbd("\u2193") + " down &middot; " +
      kbd("k") + "/" + kbd("\u2191") + " up &middot; " +
      kbd("l") + "/" + kbd("\u2192") + " open";
  } else if (document.querySelector(".back-link")) {
    hint.innerHTML = kbd("h") + "/" + kbd("\u2190") + " back";
  }
  if (hint.innerHTML) {
    var footer = document.querySelector(".site-footer");
    if (footer) footer.parentNode.insertBefore(hint, footer);
  }
})();
