import re

import stdnum.iban

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from .mbank_request import MBankStatementStatus, MBankApiException


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    x_mbank_status = fields.Selection(
        selection=[
            (MBankStatementStatus.PENDING, 'Pending'),
            (MBankStatementStatus.TO_EDIT, 'To Edit'),
            (MBankStatementStatus.TO_AUTH, 'To Auth'),
            (MBankStatementStatus.IN_AUTH, 'In Auth'),
            (MBankStatementStatus.AUTHORIZED, 'Authorized'),
            (MBankStatementStatus.IN_REALIZ, 'In Realization'),
            (MBankStatementStatus.REALIZED, 'Realization'),
            (MBankStatementStatus.DENIED, 'Denied'),
            (MBankStatementStatus.PROCESSED, 'Processed'),
            (MBankStatementStatus.CONDITIONAL, 'Conditional'),
            (MBankStatementStatus.REALIZ_AND_COND, 'Realized and Conditional'),
            (MBankStatementStatus.SIGN_VERIFY, 'To Sign Verify'),
            (MBankStatementStatus.REALIZED, 'Realized'),
            (MBankStatementStatus.CONFIRMED, 'Confirmed (PZ)'),
            (MBankStatementStatus.STOPPED, 'Pending - stop transaction'),
            (MBankStatementStatus.STOP_CUST_C, 'Pending - stop client'),
            (MBankStatementStatus.STOP_ACC_C, 'Pending - stop account'),
            (MBankStatementStatus.VALIDATED, 'Validated - mass'),
            (MBankStatementStatus.DELETED, 'Deleted'),
        ],
        string='mBank Status',
    )
    x_mbank_batch_id = fields.Char(string='mBank Batch Id')
    x_mbank_show_payment_button = fields.Boolean(compute='x_mbank_compute_show_payment_button')

    @api.onchange('x_mbank_batch_id', 'payment_method_id')
    def x_mbank_compute_show_payment_button(self):
        self.x_mbank_show_payment_button = False
        if (
            not self.x_mbank_batch_id
            and self.payment_ids
            and self.payment_method_id.id
            in (
                self.env.ref('trilab_mbank.mbank_payment_method').id,
                self.env.ref('trilab_mbank.mbank_split_payment_method').id,
            )
        ):
            self.x_mbank_show_payment_button = True

    def x_mbank_domestic_transfer(self):
        self.ensure_one()

        try:
            self._x_mbank_domestic_transfer()
        except (AssertionError, MBankApiException) as err:
            raise ValidationError(err) from err

    def _x_mbank_validate_payments(self):
        self.ensure_one()

        assert self.batch_type == 'outbound', _('Incorrect batch type')
        assert self.payment_ids, _("Batch can't be empty")

        invalid_partner_banks = set()

        for payment in self.payment_ids:
            assert payment.currency_id.id == self.env.ref('base.PLN').id, _('Only PLN at the moment')

            assert payment.journal_id.bank_account_id.id == self.journal_id.bank_account_id.id, _(
                'Different Batch and Payment bank accounts'
            )

            assert payment.payment_method_id.id == self.payment_method_id.id, _(
                'Different Batch and Payment payment methods'
            )

            assert payment.partner_bank_id.sanitized_acc_number, _(
                'Recipient Bank Account is required for %s', payment.partner_id.display_name
            )

            assert payment.journal_id.bank_account_id.sanitized_acc_number, _(
                'Account Number is not set for this journal bank account.'
            )

            iban_acc_number = payment.partner_bank_id.sanitized_acc_number
            if not iban_acc_number[:2].isalpha():
                iban_acc_number = f'PL{iban_acc_number}'

            if not stdnum.iban.is_valid(iban_acc_number):
                invalid_partner_banks.add(payment.partner_bank_id)

        assert not invalid_partner_banks, _(
            'Invalid account numbers for:\n%s',
            '\n'.join(f'- {_x.partner_id.display_name} - {_x.acc_number}' for _x in invalid_partner_banks)
        )

    def _x_mbank_domestic_transfer(self):
        self._x_mbank_validate_payments()

        transactions = []
        for payment in self.payment_ids:
            connected_invoices = payment.mapped('reconciled_bill_ids')
            if len(connected_invoices) == 1:
                payment_date = (
                    connected_invoices.invoice_date_due
                    if connected_invoices.invoice_date_due >= fields.Date.today()
                    else fields.Date.today()
                )
            else:
                payment_date = payment.date

            if payment.payment_method_id.id == self.env.ref('trilab_mbank.mbank_split_payment_method').id:
                if len(payment.reconciled_bill_ids.ids) != 1:
                    raise ValidationError(
                        _('More than one invoice connected with payment %s or no invoices connected', payment.name)
                    )
                split_payment_data = {'reconciled_bill_ids': payment.reconciled_bill_ids, 'vat': payment.partner_id.vat}

            else:
                split_payment_data = False

            # noinspection PyProtectedMember
            transactions.append(
                {
                    'unique_id': payment.id,
                    'amount': payment.amount,
                    'partner_name': payment.partner_id.name,
                    'partner_acc_num': re.sub(r'\D', '', payment.partner_bank_id.sanitized_acc_number),
                    'description': payment.ref or payment.name,
                    'acc_number': payment.journal_id.bank_account_id.sanitized_acc_number,
                    'currency_code': payment.currency_id.name,
                    'country': payment.partner_id.country_id.code,
                    'street_name': payment.partner_id.street,
                    'post_code': payment.partner_id.zip,
                    'city': payment.partner_id.city,
                    'address': payment.partner_id._display_address(without_company=True),
                    'exec_date': payment_date,
                    'split_payment_data': split_payment_data,
                    'reference': payment.payment_reference,
                }
            )

        req = self.journal_id.x_mbank_get_api_client()

        req.auth(**self.journal_id.x_mbank_get_auth_kwargs())

        self.x_mbank_batch_id = req.import_transactions(
            unique_id=self.id,
            transactions=transactions,
            company_name=self.journal_id.company_id.display_name,
            batch_name=self.name,
        )
        self.x_mbank_status = req.get_import_status(self.x_mbank_batch_id) or MBankStatementStatus.PENDING

    @api.model
    def x_mbank_check_status(self):
        exclude_mbank_status = (
            MBankStatementStatus.REALIZED,
            MBankStatementStatus.DENIED,
            MBankStatementStatus.REALIZ_AND_COND,
        )

        batch_ids = self.search(
            [
                (
                    'journal_id',
                    'in',
                    self.env['account.journal'].search([('bank_statements_source', '=', 'mbank')]).ids,
                ),
                (
                    'payment_method_id',
                    'in',
                    (
                        self.env.ref('trilab_mbank.mbank_payment_method').id,
                        self.env.ref('trilab_mbank.mbank_split_payment_method').id,
                    ),
                ),
                ('x_mbank_status', 'not in', exclude_mbank_status),
                ('x_mbank_batch_id', '!=', False),
            ]
        )

        for journal_id, journal_batches in tools.groupby(batch_ids, key=lambda x: x.journal_id):
            req = journal_id.x_mbank_get_api_client()
            req.auth(**journal_id.x_mbank_get_auth_kwargs())
            for batch in journal_batches:
                batch.x_mbank_status = req.get_import_status(batch.x_mbank_batch_id)
