(() => {
  const projectGrid = document.querySelector("#project-grid");
  const mapList = document.querySelector("#map-list");
  const horizonGrid = document.querySelector("#horizon-grid");
  const esc = (value) => String(value).replace(/[&<>"]/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[char]));
  const renderProjects = (projects) => {
    projectGrid.innerHTML = projects.map((project) =>
      "<article class=\"project-card\" id=\"" + esc(project.id) + "\">" +
      "<div class=\"project-top\"><span class=\"project-type\">" + esc(project.type) + "</span><span class=\"project-status\"><i class=\"status-dot " + esc(project.statusTone) + "\"></i>" + esc(project.status) + "</span></div>" +
      "<h3>" + esc(project.title) + "</h3><p class=\"project-period\">" + esc(project.period) + "</p>" +
      "<div class=\"project-label\">核心问题</div><p>" + esc(project.question) + "</p>" +
      "<div class=\"project-label\">我的工作</div><p class=\"project-contribution\">" + esc(project.contribution) + "</p>" +
      "<div class=\"project-evidence\"><div class=\"project-label\">证据与边界</div><p><strong>" + esc(project.evidenceLabel) + "</strong> " + esc(project.evidence) + "</p></div>" +
      "<div class=\"project-foot\"><span>" + esc(project.relation) + "</span><span>" + esc(project.visibility) + "</span></div></article>"
    ).join("");
  };
  const renderMapList = (nodes) => {
    mapList.innerHTML = nodes.map((node) => "<a class=\"map-list-item\" href=\"#" + esc(node.anchor) + "\"><i class=\"legend-dot " + esc(node.tone) + "\"></i><span><strong>" + esc(node.title) + "</strong><br>" + esc(node.description) + "</span></a>").join("");
  };
  const renderHorizon = (items) => {
    horizonGrid.innerHTML = items.map((item) => "<article class=\"horizon-card\" id=\"" + esc(item.id) + "\"><div class=\"horizon-kicker\">" + esc(item.kicker) + "</div><h3>" + esc(item.title) + "</h3><p class=\"horizon-question\">" + esc(item.question) + "</p><p>" + esc(item.body) + "</p><div class=\"horizon-tags\">" + item.tags.map((tag) => "<span>" + esc(tag) + "</span>").join("") + "</div></article>").join("");
  };
  Promise.allSettled([
    fetch("../data/projects.zh-CN.json?v=1", {cache: "no-store"}).then((response) => response.json()),
    fetch("../data/research-map.zh-CN.json?v=1", {cache: "no-store"}).then((response) => response.json()),
    fetch("../data/horizon.zh-CN.json?v=1", {cache: "no-store"}).then((response) => response.json())
  ]).then(([projects, map, horizon]) => {
    if (projects.status === "fulfilled") renderProjects(projects.value);
    if (map.status === "fulfilled") renderMapList(map.value.nodes);
    if (horizon.status === "fulfilled") renderHorizon(horizon.value);
  });
})();
