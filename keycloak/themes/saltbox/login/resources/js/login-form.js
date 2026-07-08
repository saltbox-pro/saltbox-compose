const initLoginForm = () => {
  const form = document.getElementById("kc-form-login");
  const loginButton = document.getElementById("kc-login");

  if (!form || !loginButton) {
    return;
  }

  const handleSubmit = () => {
    window.sbSaveAppLocale?.(document.documentElement.lang);
    loginButton.disabled = true;
    loginButton.classList.add("sb-btn--loading");
    loginButton.setAttribute("aria-busy", "true");
  };

  form.addEventListener("submit", handleSubmit);
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLoginForm);
} else {
  initLoginForm();
}
