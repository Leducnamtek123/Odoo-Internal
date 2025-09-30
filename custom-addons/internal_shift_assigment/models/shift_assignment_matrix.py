from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta, datetime
from io import BytesIO
import base64
import xlsxwriter


class ShiftAssignmentMatrix(models.Model):
	_name = 'shift.assignment.matrix'
	_description = 'Shift Assignment Matrix'

	name = fields.Char(string=_('Name'))
	start_date = fields.Date(string=_('Start Date'))
	end_date = fields.Date(string=_('End Date'))
	employee_ids = fields.Many2many('hr.employee', string=_('Employees'))
	line_ids = fields.One2many('shift.assignment.matrix.line', 'matrix_id', string=_('Lines'))
	excel_file = fields.Binary(string=_('Excel File'), attachment=False)
	state = fields.Selection([
		('draft', _('Draft')),
		('to_approve', _('To Approve')),
		('approved', _('Approved')),
		('cancel', _('Cancelled')),
	], string=_('Status'), default='draft', required=True, readonly=True, copy=False, tracking=True)

	@api.onchange('start_date')
	def _onchange_start(self):
		if self.start_date and not self.end_date:
			# Default to 7 days but allow user to change
			self.end_date = self.start_date + timedelta(days=6)
		# Also update default name when dates are available
		if self.start_date and self.end_date and not self.name:
			self.name = self._build_default_name(self.start_date, self.end_date)

	@api.onchange('end_date')
	def _onchange_end(self):
		# Update default name when user sets the end date after start date
		if self.start_date and self.end_date and not self.name:
			self.name = self._build_default_name(self.start_date, self.end_date)

	def _build_default_name(self, start_date, end_date):
		"""Return default name like: "Shift dd/mm/YYYY to dd/mm/YYYY"""
		try:
			start = fields.Date.to_date(start_date).strftime('%d/%m/%Y')
			end = fields.Date.to_date(end_date).strftime('%d/%m/%Y')
			return _('Shift %s to %s') % (start, end)
		except Exception:
			return False

	def _prepare_lines(self):
		self.ensure_one()
		# If missing critical info, do nothing (preserve existing lines)
		if not self.start_date or not self.end_date or not self.employee_ids:
			return

		# Build desired key set: (employee_id, date_str) - sorted by date and employee
		desired_keys = []
		date_cursor = self.start_date
		while date_cursor <= self.end_date:
			date_str = fields.Date.to_string(date_cursor)
			for emp in self.employee_ids:
				# Only add if employee has a valid ID (not NewId)
				if isinstance(emp.id, int):
					desired_keys.append((emp.id, date_str))
			date_cursor += timedelta(days=1)
		
		# Sort by employee_id first, then by date
		# Only sort if we have valid keys
		if desired_keys:
			desired_keys.sort(key=lambda x: (x[0], x[1]))
		desired_keys_set = set(desired_keys)

		# Index existing lines by key to preserve their values
		existing_by_key = {}
		lines_to_remove = []
		for line in self.line_ids:
			line_date_str = fields.Date.to_string(line.date) if line.date else False
			if line.employee_id and line_date_str and isinstance(line.employee_id.id, int):
				key = (line.employee_id.id, line_date_str)
				if key in desired_keys_set:
					existing_by_key[key] = line
				else:
					# Mark line for removal if employee is no longer in the matrix
					lines_to_remove.append(line.id)

		commands = []
		
		# Remove lines for employees no longer in the matrix
		for line_id in lines_to_remove:
			commands.append((2, line_id))
		
		# Add missing lines; keep existing ones to preserve calendar_id values
		for emp_id, date_str in desired_keys:
			if (emp_id, date_str) not in existing_by_key:
				# Only create commands if matrix has a valid ID
				if isinstance(self.id, int):
					commands.append((0, 0, {
						'employee_id': emp_id,
						'date': date_str,
						'matrix_id': self.id, 
					}))

		if commands:
			self.line_ids = commands

	def action_prepare(self):
		# No longer needed explicitly; kept for backward compatibility
		if not self.line_ids and self.start_date and self.end_date and self.employee_ids:
			self._prepare_lines()
		if self.id:
			return {
				'type': 'ir.actions.act_window',
				'name': _('Shift Assignment Matrix'),
				'res_model': 'shift.assignment.matrix',
				'view_mode': 'form',
				'res_id': self.id,
			}
		return False

	def action_open_import_wizard(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'shift.assignment.matrix.import.wizard',
			'view_mode': 'form',
			'view_id': self.env.ref('shift_matrix.view_shift_assignment_matrix_import_wizard_form').id,
			'target': 'new',
			'context': {
				'default_matrix_id': self.id,
			},
		}

	def action_template(self):
		self.ensure_one()
		# Prepare workbook in memory
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(_('Template'))
		# Formats
		header_format = workbook.add_format({
			'bold': True,
			'align': 'center',
			'valign': 'vcenter',
			'font_size': 12,
			'bg_color': '#D3D3D3',
			'border': 1,
		})
		data_format = workbook.add_format({
			'align': 'left',
			'valign': 'vcenter',
			'font_size': 11,
			'border': 1,
		})
		# Build date headers from range
		if not self.start_date or not self.end_date:
			raise UserError(_('Please set Start Date and End Date.'))
		date_list = []
		cursor = self.start_date
		while cursor <= self.end_date:
			date_list.append(cursor)
			cursor += timedelta(days=1)
		# Headers: first column label, then dates dd/mm/YYYY
		worksheet.write(0, 0, _('Employee Name'), header_format)
		for idx, d in enumerate(date_list, start=1):
			worksheet.write(0, idx, d.strftime('%d/%m/%Y'), header_format)
		# Employee rows and existing values
		# Index existing lines once for quick lookup
		lines_by_employee_date = {}
		for line in self.line_ids:
			if not line.employee_id or not line.date:
				continue
			lines_by_employee_date[(line.employee_id.id, fields.Date.to_date(line.date))] = line
		row_idx = 1
		for employee in self.employee_ids:
			worksheet.write(row_idx, 0, employee.name, data_format)
			col_idx = 1
			for d in date_list:
				line = lines_by_employee_date.get((employee.id, d))
				if line and line.calendar_id:
					worksheet.write(row_idx, col_idx, line.calendar_id.name, data_format)
				col_idx += 1
			row_idx += 1
		workbook.close()
		excel_data = output.getvalue()
		output.close()
		filename = 'ShiftMatrixTemplate.xlsx'
		self.excel_file = base64.b64encode(excel_data)
		return {
			'type': 'ir.actions.act_url',
			'name': _('Excel Template'),
			'url': '/web/content?model={}&id={}&field=excel_file&filename={}&download=true'.format(
				self._name, self.id, filename
			),
			'target': 'self',
		}

	def action_import_lines(self):
		self.ensure_one()
		# Deprecated in favor of export flow; keep for backward compatibility if referenced elsewhere
		return self.action_export_lines()

	def action_export_lines(self):
		# Redirect export to the same file as template (pre-filled)
		return self.action_template()

	def action_set_to_draft(self):
		for rec in self:
			rec.state = 'draft'
		return True

	def action_submit(self):
		for rec in self:
			# Ensure core data is present and matrix is fully built
			if not rec.start_date or not rec.end_date or not rec.employee_ids:
				raise UserError(_('Please set Start Date, End Date and Employees before submitting.'))
			rec._prepare_lines()
			rec.state = 'to_approve'
		return True

	def action_approve(self):
		for rec in self:
			# Validate completeness: each employee/date must have a shift selected
			# missing = rec.line_ids.filtered(lambda l: not l.calendar_id)
			# if missing:
			# 	# Build a concise error message (first 10 missing)
			# 	preview = []
			# 	for line in missing[:10]:
			# 		preview.append('%s - %s' % (line.employee_id.name or '-', fields.Date.to_string(line.date)))
			# 	more = '' if len(missing) <= 10 else _(' (+%s more)') % (len(missing) - 10)
			# 	raise UserError(_('Some shifts are missing. Please fill all cells before approval.\nMissing for:\n%s%s') % ('\n'.join(preview), more))
			rec.state = 'approved'
		return True

	def action_cancel(self):
		for rec in self:
			rec.state = 'cancel'
		return True

	@api.onchange('start_date', 'end_date', 'employee_ids')
	def _onchange_build_matrix(self):
		# Avoid overwriting unsaved edits: only build if there are no lines yet
		if not self.line_ids:
			self._prepare_lines()

	@api.model
	def create(self, vals):
		# Ensure matrix is built on first creation
		record = super().create(vals)
		if record.start_date and record.end_date and record.employee_ids:
			record._prepare_lines()
		return record

	def write(self, vals):
		# Prevent editing non-draft records (except state transitions)
		if any(rec.state != 'draft' for rec in self):
			# Allow harmless updates in non-draft, like generating export file
			blocked_fields = set(vals.keys()) - {'state', 'excel_file'}
			if blocked_fields:
				raise UserError(_('Only Draft records can be edited.'))
		# Ensure matrix is rebuilt when updating
		result = super().write(vals)
		if any(field in vals for field in ['start_date', 'end_date', 'employee_ids']):
			self._prepare_lines()
		return result


class ShiftAssignmentMatrixLine(models.Model):
	_name = 'shift.assignment.matrix.line'
	_description = 'Shift Assignment Matrix Line'
	_order = 'employee_id, date'

	matrix_id = fields.Many2one('shift.assignment.matrix', string=_('Matrix'), ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string=_('Employee'), required=True)
	date = fields.Date(string=_('Date'), required=True)
	date_text = fields.Char(string=_('Date (Text)'), compute='_compute_date_text')
	calendar_id = fields.Many2one('resource.calendar', string=_('Shift (Calendar)'))

	@api.depends('date')
	def _compute_date_text(self):
		for rec in self:
			if rec.date:
				# Render dd-mm-yyyy for UI axis labels
				try:
					rec.date_text = fields.Date.to_date(rec.date).strftime('%d-%m-%Y')
				except Exception:
					rec.date_text = fields.Date.to_string(rec.date)
			else:
				rec.date_text = False



