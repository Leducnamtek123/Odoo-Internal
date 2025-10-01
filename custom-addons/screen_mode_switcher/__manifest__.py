# __manifest__.py
{
    'name': 'Web Dark Mode Toggle',
    'version': '19.0.1.0.0',
    'category': 'Web',
    'summary': 'Add dark mode toggle to user menu with checkbox, persists in localStorage',
    'description': """
        This module adds a Dark Mode toggle checkbox to the Odoo user menu.
        - Toggles between light and dark themes
        - Stores preference in browser localStorage
        - Applies CSS class 'dark-mode' to body
        - Includes basic dark mode CSS overrides
    """,
    'author': 'Your Name',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'screen_mode_switcher/static/src/scss/dark_mode.scss',
            'screen_mode_switcher/static/src/scss/switch_mode.scss',
            'screen_mode_switcher/static/src/js/dark_mode_menu.js'
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}