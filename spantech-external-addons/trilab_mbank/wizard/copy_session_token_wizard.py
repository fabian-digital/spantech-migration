import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from odoo.addons.trilab_mbank.models.mbank_request import MBankAuthMethods

_logger = logging.getLogger(__name__)


class CopySessionTokenWizard(models.TransientModel):
    _name = 'trilab_mbank.copy.session.token.wizard'
    _description = 'Trilab mBank Copy Session Token Wizard'

    journal_ids = fields.Many2many(
        'account.journal', default=lambda self: self.env.context.get('active_ids', []), readonly=True
    )

    source_journal_id = fields.Many2one('account.journal')

    mbank_dik = fields.Char(compute='_compute_mbank_auth_info')
    mbank_user_id = fields.Char(compute='_compute_mbank_auth_info')

    def copy_session_token(self):
        self.journal_ids.write({'x_mbank_session_token': self.source_journal_id.x_mbank_session_token})
        _logger.info(f'Copied x_mbank_session_token from {self.source_journal_id} to {self.journal_ids}')

    @api.onchange('journal_ids')
    def _check_onchange_journal_ids(self):
        diks = self.journal_ids.mapped('x_mbank_dik')
        user_ids = self.journal_ids.mapped('x_mbank_user_id')
        methods = self.journal_ids.mapped('x_mbank_auth_method')
        if (
            len(set(diks)) != 1
            or len(set(user_ids)) != 1
            or any(method != MBankAuthMethods.BACKGROUND_SESSION.value for method in methods)
        ):
            raise ValidationError(
                _('All Journals have to have same DIK and User ID and Long term Session Authentication Method')
            )

    @api.depends('journal_ids')
    def _compute_mbank_auth_info(self):
        for wizard in self:
            wizard.mbank_dik = wizard.mbank_user_id = False

            if self.journal_ids:
                journal_id = self.journal_ids[0]
                wizard.mbank_dik = journal_id.x_mbank_dik
                wizard.mbank_user_id = journal_id.x_mbank_user_id
