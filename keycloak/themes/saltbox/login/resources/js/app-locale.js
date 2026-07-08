const APP_LOCALES = ["en", "ru"];
const STORAGE_KEY = "currentLocale";

window.sbSaveAppLocale = (locale) => {
  if (locale && APP_LOCALES.includes(locale)) {
    localStorage.setItem(STORAGE_KEY, locale);
  }
};
