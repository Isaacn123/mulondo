(function ($) {
  "use strict";

  var $sidebar = $("#accordionSidebar");
  if (!$sidebar.length) return;

  function $toggleFor($collapse) {
    var id = $collapse.attr("id");
    if (!id) return $();
    return $sidebar.find('[data-toggle="collapse"][data-target="#' + id + '"]');
  }

  function syncToggle($collapse) {
    var $toggle = $toggleFor($collapse);
    if (!$toggle.length) return;
    var open = $collapse.hasClass("show");
    $toggle.toggleClass("collapsed", !open);
    $toggle.attr("aria-expanded", open ? "true" : "false");
  }

  function syncAll() {
    $sidebar.find(".collapse").each(function () {
      syncToggle($(this));
    });
  }

  function closeNestedWithoutActive() {
    var $pages = $("#collapsePages");
    if (!$pages.length) return;
    $pages.find(".collapse-inner > .collapse.show").each(function () {
      var $sub = $(this);
      if (!$sub.find(".collapse-item.active").length) {
        $sub.removeClass("show");
        syncToggle($sub);
      }
    });
  }

  syncAll();
  closeNestedWithoutActive();

  $sidebar.find(".collapse").on("shown.bs.collapse hidden.bs.collapse", function () {
    syncToggle($(this));
  });

  // Leaf links: collapse unrelated top-level sections (keep current branch open).
  $sidebar.find(".collapse-item[href]:not([href='#'])").on("click", function () {
    var href = this.getAttribute("href");
    if (!href || href === "#") return;
    var $branch = $(this).closest(".collapse");
    $sidebar.find("> .nav-item > .collapse.show").each(function () {
      var $panel = $(this);
      if (!$branch.length || !$branch.is($panel) && !$branch.closest($panel).length) {
        $panel.removeClass("show");
        syncToggle($panel);
      }
    });
  });
})(jQuery);
