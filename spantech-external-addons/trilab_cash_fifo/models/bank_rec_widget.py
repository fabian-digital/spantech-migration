from odoo import api, fields, models


class BankRecWidget(models.Model):
    _inherit = 'bank.rec.widget'

    x_show_post_move_btn = fields.Boolean(compute='_x_compute_show_post_move_btn')

    @api.depends('st_line_id', 'state')
    def _x_compute_show_post_move_btn(self):
        for wizard_id in self:
            wizard_id.x_show_post_move_btn = (
                wizard_id.st_line_id.journal_id.x_cash_valuation_method and wizard_id.move_id.state == 'draft'
            )

    @api.depends('st_line_id')
    def _compute_state(self):
        super()._compute_state()

        for wizard_id in self:
            if wizard_id.st_line_id.journal_id.x_cash_valuation_method and wizard_id.move_id.state == 'draft':
                wizard_id.state = 'invalid'

    def x_button_post_move(self):
        self.ensure_one()
        self.st_line_id.move_id.to_check = False
        self.st_line_id.move_id.action_post()
        self.next_action_todo = {'type': 'refresh_statement_line'}
        self.invalidate_recordset(fnames=['to_check'])
