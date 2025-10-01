// dark_mode_backend/static/src/js/dark_mode_menu.js
/** @odoo-module **/

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { markup } from "@odoo/owl";

const DARK_MODE_CLASS = "dark-mode";
const THEME_KEY = "odoo_dark_theme";

// Cookie handling functions
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function darkModeItem(env) {
    const savedTheme = getCookie(THEME_KEY) || "light";
    const isDark = savedTheme === "dark";
    return {
        type: "item",
        id: "dark_mode",
        description: markup`
            <div class="d-flex align-items-center justify-content-between p-0 w-100">
                <span>${_t("Dark Mode")}</span>
                <label class="o-switch ms-2">
                    <input type="checkbox" class="o-switch-input dark-mode-toggle" ${isDark ? "checked" : ""} />
                    <span class="o-switch-slider"></span>
                </label>
            </div>`,
        callback: () => {
            // Fallback toggle if clicked on the item outside the switch
            toggleTheme(env);
        },
        sequence: 55,
    };
}

// Global event listener for switcher change (direct click on switch)
document.addEventListener("change", (event) => {
    if (event.target.matches(".dark-mode-toggle")) {
        const newTheme = event.target.checked ? "dark" : "light";
        setCookie(THEME_KEY, newTheme, 365); // Store for 1 year
        document.body.classList.toggle(DARK_MODE_CLASS, newTheme === "dark");
    }
}, true);

function toggleTheme(env) {
    const currentTheme = getCookie(THEME_KEY) || "light";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    setCookie(THEME_KEY, newTheme, 365);
    document.body.classList.toggle(DARK_MODE_CLASS, newTheme === "dark");
    // Trigger user menu update to re-render the checkbox state immediately
    if (env && env.services && env.services.ui && env.services.ui.bus) {
        env.services.ui.bus.trigger("USER_MENU:UPDATE");
    } else {
        // Fallback: Reload page to ensure update (not ideal, but works if env not available)
        location.reload();
    }
}

// Initialize theme on load
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeTheme);
} else {
    initializeTheme();
}

// Khi trang load, đồng bộ switch với cookie
function initializeTheme() {
    const savedTheme = getCookie(THEME_KEY) || "light";
    const isDark = savedTheme === "dark";

    document.body.classList.toggle(DARK_MODE_CLASS, isDark);

    // Cập nhật trạng thái checkbox nếu đã render
    const checkbox = document.querySelector(".dark-mode-toggle");
    if (checkbox) {
        checkbox.checked = isDark;
    }
}


registry.category("user_menuitems").add("dark_mode", darkModeItem);