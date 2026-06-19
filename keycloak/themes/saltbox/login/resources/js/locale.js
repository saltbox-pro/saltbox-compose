const initLocaleSwitcher = () => {
  const localeRoot = document.getElementById("sb-locale");

  if (!localeRoot) {
    return;
  }

  const trigger = localeRoot.querySelector(".sb-locale__trigger");
  const menu = localeRoot.querySelector(".sb-locale__menu");

  if (!trigger || !menu) {
    return;
  }

  const closeMenu = () => {
    menu.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  };

  const openMenu = () => {
    menu.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
  };

  const handleTriggerClick = (event) => {
    event.stopPropagation();

    if (menu.hidden) {
      openMenu();
      return;
    }

    closeMenu();
  };

  const handleDocumentClick = (event) => {
    if (!localeRoot.contains(event.target)) {
      closeMenu();
    }
  };

  const handleDocumentKeydown = (event) => {
    if (event.key === "Escape") {
      closeMenu();
    }
  };

  trigger.addEventListener("click", handleTriggerClick);
  document.addEventListener("click", handleDocumentClick);
  document.addEventListener("keydown", handleDocumentKeydown);
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLocaleSwitcher);
} else {
  initLocaleSwitcher();
}
