{
	'name': 'Shift Assignment Matrix',
    'version': '19.0.1.0.0',
	'summary': 'Assign worker shifts on an Employee x Date matrix using web_widget_x2many_2d_matrix',
    "category": "INTERNAL",
	'license': 'AGPL-3',
	'depends': ['base', 'hr', 'web_widget_x2many_2d_matrix'],
	'data': [
		'security/ir.model.access.csv',
		'views/shift_assignment_matrix_views.xml',
		'views/shift_assignment_matrix_wizard_views.xml',
	],
	'assets': {
		'web.assets_backend': [
			'internal_shift_assigment/static/src/scss/matrix_theme.scss',
		],
	},
	'external_dependencies': {
		'python': ['openpyxl', 'xlsxwriter']
	},
	'installable': True,
	'application': False,
    "auto_install": False,
}

