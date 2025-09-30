/** @odoo-module **/

// Synchronize Odoo UI dark mode based on COOKIE `color_scheme`
// and toggle CSS hook classes `o-color-scheme-dark` / `o-color-scheme-light` on <html> and <body>.

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
        return parts.pop().split(';').shift();
    }
    return null;
}

function applyColorSchemeFromStorage() {
    try {
        const colorScheme = getCookie("color_scheme");
        const isDark = colorScheme === "dark";
        const isLight = colorScheme === "light";
        const root = document.documentElement;
        const body = document.body;
        if (!root || !body) {
            return;
        }
        // Ensure explicit override classes
        root.classList.toggle("o-color-scheme-dark", isDark);
        body.classList.toggle("o-color-scheme-dark", isDark);
        root.classList.toggle("o-color-scheme-light", isLight);
        body.classList.toggle("o-color-scheme-light", isLight);
        if (!isDark && !isLight) {
            root.classList.remove("o-color-scheme-dark", "o-color-scheme-light");
            body.classList.remove("o-color-scheme-dark", "o-color-scheme-light");
        }
    } catch (e) {
        // Fail silently; theming is non-critical
    }
}

// Apply on initial load
document.addEventListener("DOMContentLoaded", applyColorSchemeFromStorage, { once: true });

// Cookies do not emit events; keep it in sync periodically and on visibility change
let __colorSchemeSyncInterval = null;
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") {
        applyColorSchemeFromStorage();
    }
});

// Lightweight polling (every 2s) to reflect changes done by Odoo UI
__colorSchemeSyncInterval = window.setInterval(applyColorSchemeFromStorage, 2000);


