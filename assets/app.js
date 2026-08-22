/* 강산재 — 스크롤 리빌 및 헤더 전환 */
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 스크롤 진입 시 요소 나타내기
  var items = document.querySelectorAll(".reveal");
  if (reduce || !("IntersectionObserver" in window)) {
    items.forEach(function (el) { el.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  }

  // 메인 페이지 헤더: 히어로를 지나면 밝은 배경으로 전환
  var header = document.querySelector(".header");
  if (header && !header.classList.contains("static")) {
    var onScroll = function () {
      header.classList.toggle("solid", window.scrollY > window.innerHeight * 0.82);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // 모바일 메뉴: 항목 선택 시 닫기
  var toggle = document.getElementById("nav");
  if (toggle) {
    document.querySelectorAll(".gnb a").forEach(function (a) {
      a.addEventListener("click", function () { toggle.checked = false; });
    });
  }
})();
