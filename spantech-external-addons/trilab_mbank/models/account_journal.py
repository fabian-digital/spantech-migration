import logging
import os
from collections import defaultdict
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .mbank_request import MBankApiException, MBankAuthMethods, MBankRequest

_logger = logging.getLogger(__name__)

NUMBER_OF_TRIES = 20


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    x_mbank_dik = fields.Char('DIK')
    x_mbank_user_id = fields.Char('User ID')
    x_mbank_test = fields.Boolean('Test', default=True)
    x_mbank_auth_method = fields.Selection(
        selection=[
            (MBankAuthMethods.SIGNATURE.value, 'Signature'),
            (MBankAuthMethods.TOKEN.value, 'Token'),
            (MBankAuthMethods.BACKGROUND_SESSION.value, 'Long term Session'),
        ],
        string='Authentication Method',
    )
    x_mbank_app_cert = fields.Binary('App Cert File', help='.p12 file containing private key and certificate')
    x_mbank_app_cert_filename = fields.Char(string='App Cert Filename')
    x_mbank_app_cert_password = fields.Char(string='App Cert Password')
    x_mbank_session_token = fields.Char(string='Session Token', readonly=True)
    x_mbank_enable_logging = fields.Boolean('Enable Logging')

    @api.constrains('x_mbank_app_cert', 'outbound_payment_method_line_ids')
    def _x_constrains_x_mbank_cert_file(self):
        _logger.debug('IN CONSTRAINS')
        for journal in self.filtered(lambda x: x.bank_statements_source == 'mbank'):
            error_msg = _('.p12 files containing private key and certificate required.')
            if not journal.x_mbank_app_cert:
                if (
                    self.env.ref('trilab_mbank.mbank_payment_method').id
                    in journal.outbound_payment_method_line_ids.payment_method_id.ids
                ):
                    if journal.x_mbank_auth_method == MBankAuthMethods.SIGNATURE.value:
                        raise ValidationError(error_msg)

                if journal.x_mbank_auth_method == MBankAuthMethods.SIGNATURE.value:
                    if journal.bank_statements_source == 'mbank':
                        raise ValidationError(error_msg)

            if journal.x_mbank_app_cert and not journal.x_mbank_app_cert_filename.endswith('.p12'):
                raise ValidationError(error_msg)

    @api.constrains('x_mbank_test', 'x_mbank_auth_method')
    def _x_check_auth_method(self):
        if any(
            not journal.x_mbank_test and journal.x_mbank_auth_method not in ('sign', 'background_session')
            for journal in self
        ):
            raise ValidationError(
                _('In Production Environment only Signature Authentication  or Long term Session is allowed.')
            )

    @api.constrains('bank_account_id', 'bank_statements_source')
    def _x_check_bank_account_type(self):
        for journal in self:
            if journal.bank_statements_source == 'mbank' and journal.bank_account_id.acc_type != 'iban':
                raise ValidationError(_('The bank account of a mBank journal must be in IBAN type.'))

    def __get_bank_statements_available_sources(self):
        res = super(AccountJournal, self).__get_bank_statements_available_sources()
        res.append(('mbank', 'mBank Polska'))
        return res

    def x_mbank_get_att_path(self, field_name):
        attachment = (
            self.env['ir.attachment']
            .sudo()
            .search([('res_model', '=', self._name), ('res_field', '=', field_name), ('res_id', '=', self.id)], limit=1)
        )
        return os.path.join(attachment._filestore(), attachment.store_fname) if attachment else None

    def _x_mbank_stmt_to_db(self, bank, statement):
        bank_statement = {
            'journal_id': bank.id,
            'date': statement.start_balance.balance_date,
            'name': statement.statement_number,
            'balance_start': statement.start_balance.amount,
            'balance_end_real': statement.end_balance.amount,
            'line_ids': [],
        }

        for seq, transaction in enumerate(statement.transactions):
            record = {
                'sequence': seq,
                'payment_ref': transaction.description,
                'narration': transaction.title or transaction.reference or transaction.institution_reference,
                'date': transaction.booking_date,
                'partner_name': transaction.partner,
                'account_number': transaction.account_number,
                'amount': transaction.amount,
                'journal_id': bank.id,
            }

            if transaction.account_number:
                partner_bank = self.env['res.partner.bank'].search(
                    [
                        ('company_id', '=', self.env.company.id),
                        ('sanitized_acc_number', 'ilike', record['account_number']),
                    ],
                    limit=1,
                )

                if partner_bank:
                    record['partner_id'] = partner_bank.partner_id.id
                    record['partner_name'] = partner_bank.partner_id.name

            bank_statement['line_ids'].append(models.Command.create(record))

        if bank_statement['line_ids']:
            return bank_statement

    def x_mbank_get_api_client(self):
        self.ensure_one()

        assert self.bank_statements_source == 'mbank', _('Incorrect source')

        return MBankRequest(
            self.x_mbank_dik,
            self.x_mbank_user_id,
            MBankAuthMethods(self.x_mbank_auth_method),
            is_test=self.x_mbank_test,
            enable_logging=self.x_mbank_enable_logging,
        )

    def x_mbank_get_auth_kwargs(self):
        self.ensure_one()
        return dict(
            cert_file_path=self.x_mbank_get_att_path('x_mbank_app_cert'),
            cert_password=self.x_mbank_app_cert_password,
            session_token=self.x_mbank_session_token,
        )

    @api.model
    def x_mbank_download_statements(self, banks=None, date_from=None, date_to=None):
        banks = banks or self.search([('type', '=', 'bank'), ('bank_statements_source', '=', 'mbank')])
        Statement = self.env['account.bank.statement']

        if not date_from:
            date_from = fields.Date.today() - timedelta(days=1)

        if not date_to:
            date_to = fields.Date.today()

        deferred_statements = {}
        to_add_statement_numbers = defaultdict(list)

        for bank in banks:
            req = bank.x_mbank_get_api_client()

            try:
                req.auth(**bank.x_mbank_get_auth_kwargs())
                statements = req.get_statements(date_from, date_to, bank.bank_account_id.sanitized_acc_number)

            except MBankApiException as err:
                raise ValidationError(str(err)) from err

            for stmt in statements[bank.bank_account_id.sanitized_acc_number]:
                if stmt.statement_number not in to_add_statement_numbers[bank.id] and not Statement.search(
                    [('journal_id', '=', bank.id), ('name', '=', stmt.statement_number)]
                ):
                    deferred_statements.setdefault(bank.id, {'bank': bank, 'stmts': []})
                    deferred_statements[bank.id]['stmts'].append(stmt)
                    to_add_statement_numbers[bank.id].append(stmt.statement_number)

        for rec in deferred_statements.values():
            for statement in rec['stmts']:
                bank_statement = self._x_mbank_stmt_to_db(rec['bank'], statement)
                if bank_statement:
                    Statement.create(bank_statement)
