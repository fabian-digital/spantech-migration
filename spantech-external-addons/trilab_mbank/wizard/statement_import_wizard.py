from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StatementImportWizard(models.TransientModel):
    _name = 'trilab_mbank.statement.import.wizard'
    _description = 'mBank Statement Import Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    bank_account_ids = fields.Many2many('account.journal')

    @api.constrains('bank_account_ids')
    def constrains_bank_accounts_ids(self):
        if not self.bank_account_ids:
            raise ValidationError(_('Bank account is required'))

    def import_statements(self):
        self.env['account.journal'].x_mbank_download_statements(
            banks=self.bank_account_ids, date_from=self.date_from, date_to=self.date_to
        )
