(() => {
  "use strict";

  const body = document.body;

  async function loadComponent(targetId, url) {
    const target = document.getElementById(targetId);

    if (!target) {
      return;
    }

    try {
      const response = await fetch(url, { cache: "no-cache" });

      if (!response.ok) {
        throw new Error(`${url}: HTTP ${response.status}`);
      }

      target.innerHTML = await response.text();
    } catch (error) {
      console.error("CKOEPPEN Layout konnte nicht geladen werden:", error);
      target.innerHTML =
        '<div class="layout-error">Navigation konnte nicht geladen werden.</div>';
    }
  }

  function configureSidebar() {
    const activeTool = body.dataset.activeTool || "";
    const toolTitle = body.dataset.toolTitle || "CKOEPPEN TOOLBOX";

    document.querySelectorAll(".nav-link[data-tool]").forEach((link) => {
      link.classList.toggle("active", link.dataset.tool === activeTool);
    });

    const mobileTitle = document.getElementById("mobileToolTitle");

    if (mobileTitle) {
      mobileTitle.textContent = toolTitle.toUpperCase();
    }

    const menuButton = document.getElementById("menu");

    if (menuButton) {
      menuButton.addEventListener("click", () => {
        body.classList.toggle("menu-open");
      });
    }

    document.querySelectorAll(".coming-soon-link").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
      });
    });

    document.querySelectorAll(".sidebar .nav-link:not(.coming-soon-link)").forEach(
      (link) => {
        link.addEventListener("click", () => {
          body.classList.remove("menu-open");
        });
      }
    );
  }

  function configureTopbar() {
    const toolTitle = body.dataset.toolTitle || "";
    const platformTitle = document.getElementById("platformTitle");

    if (platformTitle && toolTitle) {
      platformTitle.textContent = `CKOEPPEN Toolbox · ${toolTitle}`;
    }

    const themeToggle = document.getElementById("themeToggle");

    if (!themeToggle) {
      return;
    }

    const savedTheme = localStorage.getItem("cko-theme");

    if (savedTheme === "light") {
      body.classList.add("light");
    }

    themeToggle.addEventListener("click", () => {
      body.classList.toggle("light");

      localStorage.setItem(
        "cko-theme",
        body.classList.contains("light") ? "light" : "dark"
      );
    });
  }

  async function initializeLayout() {
    await Promise.all([
      loadComponent("cko-sidebar", "/static/toolbox/components/sidebar.html"),
      loadComponent("cko-topbar", "/static/toolbox/components/topbar.html"),
    ]);

    configureSidebar();
    configureTopbar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeLayout);
  } else {
    initializeLayout();
  }
})();
