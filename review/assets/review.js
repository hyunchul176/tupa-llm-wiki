// TUPA LLM-Wiki 리뷰 HTML 공용 스크립트 — figure 클릭 시 확대(lightbox).
// 생성된 review/<주제>/index.html 이 ../assets/review.js 로 참조한다.
(function () {
  var box = document.createElement("div");
  box.className = "lightbox";
  box.innerHTML = '<img alt="figure">';
  document.addEventListener("DOMContentLoaded", function () { document.body.appendChild(box); });
  var img = box.querySelector("img");
  document.addEventListener("click", function (e) {
    var t = e.target;
    if (t && t.tagName === "IMG" && t.closest(".fig")) {
      img.src = t.currentSrc || t.src;
      box.classList.add("open");
    } else if (box.classList.contains("open")) {
      box.classList.remove("open");
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") box.classList.remove("open");
  });
})();
