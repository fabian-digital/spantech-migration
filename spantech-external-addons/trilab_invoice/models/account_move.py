import copy
import logging
from collections import defaultdict
from functools import lru_cache

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_round, format_date, formatLang, get_lang

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_correction_invoices_len = fields.Integer(compute='_x_compute_correction_invoices_len', store=False)

    x_original_invoice_line_ids = fields.Many2many(
        comodel_name='account.move.line',
        string='Original Invoice Lines',
        compute='_x_compute_original_invoice_line_ids',
        readonly=True,
        store=False,
        tracking=False,
    )

    x_corrected_invoice_line_ids = fields.One2many(
        'account.move.line',
        'move_id',
        string='Corrected Invoice lines',
        copy=False,
        readonly=True,
        compute='_x_compute_corrected_invoice_line_ids',
        inverse='_x_inverse_corrected_invoice_line_ids',
        states={'draft': [('readonly', False)]},
    )

    x_invoice_sale_date = fields.Date(string='Sale/Currency Date')
    x_invoice_duplicate_date = fields.Date(string='Duplicate Date', copy=False)

    # connected sale order (for advance invoice PDF)
    x_advance_source_id = fields.Many2one('sale.order', compute='_x_compute_advance_source_id', store=False)
    # connected sale order (for final invoice PDF)
    x_final_source_id = fields.Many2one('sale.order', compute='x_compute_advance_invoices_ids', store=False)
    # connected advance invoices (for final invoice PDF)
    x_advance_invoices_ids = fields.Many2many('account.move', compute='x_compute_advance_invoices_ids', store=False)

    x_use_ti = fields.Boolean(compute='_x_compute_use_ti', string='Technical Field: Is Poland')
    x_corrected_amount_total = fields.Float(compute='_x_compute_corrected_amount_total')

    x_amount_total = fields.Monetary(string='X Total in Currency', compute='_x_compute_amount')
    x_amount_residual = fields.Monetary(string='X Amount Due', compute='_x_compute_amount')
    x_currency_rate = fields.Float('Currency Rate', digits=(16, 4))
    x_show_currency_rate = fields.Boolean(compute='_x_compute_show_currency_rate')

    @api.depends('company_id')
    def _x_compute_use_ti(self):
        for move_id in self:
            move_id.x_use_ti = (move_id.company_id or self.env.company).x_use_ti

    @api.depends('move_type', 'state', 'x_advance_source_id', 'x_advance_invoices_ids')
    def _compute_type_name(self):
        type_name_mapping = dict(
            self._fields['move_type']._description_selection(self.env),
            out_invoice=_('Invoice'),
            out_refund=_('Correction Invoice'),
            in_invoice=_('Vendor Bill'),
            in_refund=_('Vendor Correction Invoice'),
        )

        for move_id in self:
            if not move_id.x_use_ti:
                super()._compute_type_name()
                continue

            name = None

            if move_id.move_type == 'out_invoice':
                if move_id.x_advance_invoices_ids:
                    if move_id.state == 'posted':
                        name = _('Final Invoice')

                    elif move_id.state == 'draft':
                        name = _('Draft Final Invoice')

                    elif move_id.state == 'cancel':
                        name = _('Cancelled Final Invoice')

                elif move_id.x_advance_source_id:
                    if move_id.state == 'posted':
                        name = _('Advance Invoice')

                    elif move_id.state == 'draft':
                        name = _('Pro Forma Invoice')

                    elif move_id.state == 'cancel':
                        name = _('Cancelled Advance Invoice')

                else:
                    if move_id.state == 'draft':
                        name = _('Draft Invoice')

                    elif move_id.state == 'cancel':
                        name = _('Cancelled Invoice')

            move_id.type_name = name or type_name_mapping[move_id.move_type]

    def _get_name_invoice_report(self):
        self.ensure_one()

        if self.x_use_ti:
            return 'trilab_invoice.report_invoice_document'

        return super()._get_name_invoice_report()

    # noinspection PyUnresolvedReferences,PyTypeChecker
    def x_get_final_invoice_summary(self, with_downpayments=True):
        self.ensure_one()

        if not self.is_invoice(include_receipts=True):
            return None

        tax_totals = copy.deepcopy(self.tax_totals)

        if with_downpayments or not self.x_advance_invoices_ids:
            return tax_totals

        for advance_invoice_id in self.x_advance_invoices_ids:
            advance_tax_totals = advance_invoice_id.tax_totals

            # merge structures group_by_subtotal
            for a_group_name, a_group in advance_tax_totals['groups_by_subtotal'].items():
                for group_name, group in tax_totals['groups_by_subtotal'].items():
                    if group_name == a_group_name:
                        for a_tax_group in a_group:
                            for tax_group in group:
                                if a_tax_group['tax_group_id'] == tax_group['tax_group_id']:
                                    # add values
                                    for key in (
                                        'tax_group_amount',
                                        'tax_group_base_amount',
                                        'x_tax_group_total_amount',
                                        'x_tax_group_amount_local',
                                    ):
                                        tax_group[key] += a_tax_group[key]

                                    # update formatted values
                                    tax_group['formatted_tax_group_amount'] = formatLang(
                                        self.env, tax_group['tax_group_amount'], currency_obj=self.currency_id
                                    )
                                    tax_group['formatted_tax_group_base_amount'] = formatLang(
                                        self.env, tax_group['tax_group_base_amount'], currency_obj=self.currency_id
                                    )
                                    tax_group['x_formatted_tax_group_total_amount'] = formatLang(
                                        self.env, tax_group['x_tax_group_total_amount'], currency_obj=self.currency_id
                                    )
                                    tax_group['x_formatted_tax_group_amount_local'] = formatLang(
                                        self.env,
                                        tax_group['x_tax_group_amount_local'],
                                        currency_obj=self.env.company.currency_id,
                                    )

                                    break
                            else:
                                # no matching tax group found, adding one
                                group.append(a_tax_group)

                        break
                else:
                    # no match found, append group from advance invoice
                    tax_totals['group_by_subtotal'][a_group_name] = a_group

            # merge structure of subtotals
            for a_group in advance_tax_totals['subtotals']:
                for group in tax_totals['subtotals']:
                    if a_group['name'] == group['name']:
                        group['amount'] += a_group['amount']
                        group['formatted_amount'] = formatLang(self.env, group['amount'], currency_obj=self.currency_id)
                        break
                else:
                    # no matching subtotal found
                    tax_totals['subtotals'].append(a_group)

            # update totals
            tax_totals['amount_total'] += advance_tax_totals['amount_total']
            tax_totals['amount_untaxed'] += advance_tax_totals['amount_untaxed']
            tax_totals['x_tax_amount'] += advance_tax_totals['x_tax_amount']
            tax_totals['x_tax_amount_local'] += advance_tax_totals['x_tax_amount_local']

            tax_totals['formatted_amount_total'] = formatLang(
                self.env, tax_totals['amount_total'], currency_obj=self.currency_id
            )
            tax_totals['formatted_amount_untaxed'] = formatLang(
                self.env, tax_totals['amount_untaxed'], currency_obj=self.currency_id
            )
            tax_totals['x_formatted_tax_amount'] = formatLang(
                self.env, tax_totals['x_tax_amount'], currency_obj=self.currency_id
            )
            tax_totals['x_formatted_tax_amount_local'] = formatLang(
                self.env, tax_totals['x_tax_amount_local'], currency_obj=self.env.company.currency_id
            )

        return tax_totals

    @api.depends('invoice_line_ids')
    def _x_compute_advance_source_id(self):
        for move_id in self:
            if move_id.x_use_ti:
                advance_lines = self.env['sale.order.line'].search(
                    [
                        ('is_downpayment', '=', True),
                        ('invoice_lines', 'in', move_id.invoice_line_ids.filtered(lambda line: line.credit > 0).ids),
                    ]
                )
                move_id.x_advance_source_id = advance_lines.order_id

            else:
                self.x_advance_source_id = False

    @api.depends('invoice_line_ids')
    def x_compute_advance_invoices_ids(self):
        for move_id in self:
            if move_id.x_use_ti:
                final_line_ids = self.env['sale.order.line'].search(
                    [
                        ('is_downpayment', '=', True),
                        ('invoice_lines', 'in', move_id.invoice_line_ids.filtered(lambda line: line.debit > 0).ids),
                    ]
                )
                move_id.x_advance_invoices_ids = final_line_ids.invoice_lines.filtered(
                    lambda line: line.credit > 0
                ).move_id
                move_id.x_final_source_id = (
                    False if move_id.reversed_entry_id else fields.first(final_line_ids.order_id)
                )

            else:
                self.x_advance_invoices_ids = self.x_final_source_id = False

    @api.constrains('reversed_entry_id')
    def _x_check_correction_invoice(self):
        for move_id in self.filtered('x_use_ti'):
            if move_id.reversed_entry_id and move_id.move_type in ('out_refund', 'in_refund'):
                if (
                    self.search(
                        [
                            ('move_type', 'in', ('out_refund', 'in_refund')),
                            ('reversed_entry_id', '=', self.reversed_entry_id.id),
                        ],
                        count=True,
                    )
                    > 1
                ):
                    raise ValidationError(_('It is not possible to issue two direct corrections for one invoice.'))

    def x_get_connected_corrections(self):
        selected_invoice_id = self
        correction_ids = self.browse()

        while selected_invoice_id.reversal_move_id:
            correction_ids |= selected_invoice_id.reversal_move_id
            selected_invoice_id = selected_invoice_id.reversal_move_id

        return correction_ids

    @api.depends('reversed_entry_id')
    def _x_compute_original_invoice_line_ids(self):
        for move_id in self.with_context(x_show_as_before=True):
            if (
                not move_id.x_use_ti
                or move_id.move_type not in ('in_refund', 'out_refund')
                or not move_id.reversed_entry_id
            ):
                move_id.x_original_invoice_line_ids = [fields.Command.clear()]
                continue

            move_id.x_original_invoice_line_ids = [
                fields.Command.set(
                    move_id.invoice_line_ids.filtered(
                        lambda line_id: line_id.display_type in ('product', 'line_section', 'line_note')
                        and not line_id.x_is_corrected_line
                    ).ids
                )
            ]

    @api.depends('invoice_line_ids', 'invoice_line_ids.x_is_corrected_line')
    def _x_compute_corrected_invoice_line_ids(self):
        for move_id in self:
            move_id.x_corrected_invoice_line_ids = [
                fields.Command.set(
                    move_id.invoice_line_ids.filtered_domain(
                        [
                            ('display_type', 'in', ('product', 'line_section', 'line_note')),
                            ('x_is_corrected_line', '=', True),
                        ]
                    ).ids
                )
            ]

    def _x_inverse_corrected_invoice_line_ids(self):
        for move_id in self:
            new_lines = [
                fields.Command.create(new_line.copy_data()[0])
                for new_line in move_id.x_corrected_invoice_line_ids.filtered(
                    lambda _aml_id: isinstance(_aml_id.id, models.NewId)
                )
            ]

            if new_lines:
                move_id.invoice_line_ids = new_lines

        self._x_compute_corrected_amount_total()

    @api.depends('reversal_move_id', 'move_type')
    def _x_compute_correction_invoices_len(self):
        for move_id in self:
            if move_id.move_type in ('in_invoice', 'out_invoice', 'in_refund', 'out_refund'):
                move_id.x_correction_invoices_len = len(move_id.x_get_connected_corrections())
            else:
                move_id.x_correction_invoices_len = 0

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.company.x_use_ti:
            return super().create(vals_list)

        if self.env.context.get('x_journal_id'):
            for vals in vals_list:
                vals['journal_id'] = self.env.context['x_journal_id']

        invoice_ids = super().create(vals_list)

        for move_id, vals in zip(invoice_ids, vals_list):
            if move_id.move_type == 'out_refund' and move_id.reversed_entry_id:
                if move_id.reversed_entry_id.move_type == 'out_refund':
                    # correction to the correction
                    move_id.invoice_line_ids.with_context(check_move_validity=False).unlink()
                    for line_id in move_id.reversed_entry_id.x_corrected_invoice_line_ids.with_context(
                        include_business_fields=True, check_move_validity=False
                    ):
                        line_id.copy(
                            default={'move_id': move_id.id, 'quantity': -line_id.quantity, 'x_is_corrected_line': False}
                        )
                        line_id.copy(default={'move_id': move_id.id, 'x_is_corrected_line': True})

                else:
                    for line_id in move_id.invoice_line_ids:
                        line_id.with_context(include_business_fields=True, check_move_validity=False).copy(
                            default={'move_id': move_id.id, 'quantity': -line_id.quantity, 'x_is_corrected_line': True}
                        )

        return invoice_ids

    def x_view_correction_invoices_action(self):
        self.ensure_one()

        action = None

        if self.move_type in ('in_invoice', 'out_invoice', 'in_refund', 'out_refund'):
            action = {
                'name': _('Correction Invoices'),
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
            }

            correction_ids = self.x_get_connected_corrections()

            if len(correction_ids) == 1:
                action.update({'view_mode': 'form', 'res_id': correction_ids.id})

            else:
                action['domain'] = [('id', 'in', self.x_get_connected_corrections().ids)]

        return action

    def action_reverse(self):
        self.ensure_one()

        if not self.x_use_ti or self.is_purchase_document():
            return super().action_reverse()

        rec_id = self

        if self.reversed_entry_id:
            rec_id = self.reversed_entry_id.with_context(
                active_id=self.reversed_entry_id.id, active_ids=self.reversed_entry_id.ids
            )

        action = rec_id.env.ref('account.action_view_account_move_reversal').read()[0]

        if rec_id.is_invoice():
            action['name'] = _('Credit Note')

        return action

    def action_post(self):
        if not self.env.company.x_use_ti:
            if self.filtered('x_use_ti'):
                raise UserError(_('Mixed Trilab Invoice enabled and non-enabled moves'))

            return super().action_post()

        for move_id in self:
            if move_id.move_type in ('in_invoice', 'in_receipt', 'in_refund') and not move_id.ref:
                raise ValidationError(_('Vendor invoice number is required'))

        res = super(AccountMove, self.with_context(x_block_changing_price=True)).action_post()

        # override from sale - fix down payment amount on connected sale.order line, ref #10957
        dp_line_ids = self.line_ids.sale_line_ids.filtered(lambda l_id: l_id.is_downpayment and not l_id.display_type)
        other_so_line_ids = dp_line_ids.order_id.order_line - dp_line_ids
        final_invoice_ids = set(other_so_line_ids.invoice_lines.move_id)

        for line_id in dp_line_ids:
            line_id.price_unit = sum(
                (line_id.price_unit if line_id.move_id.move_type == 'out_invoice' else -line_id.price_unit)
                * line_id.quantity
                for line_id in line_id.invoice_lines
                if line_id.move_id.state == 'posted' and line_id.move_id not in final_invoice_ids
            )

        return res

    def _post(self, soft=True):
        if not self.env.company.x_use_ti:
            if self.filtered('x_use_ti'):
                raise UserError(_('Mixed Trilab Invoice enabled and non-enabled moves'))

            return super()._post(soft)

        if self.filtered(lambda _am_id: _am_id.is_purchase_document(True)) and self.filtered(
            lambda _am_id: _am_id.is_sale_document()
        ):
            raise UserError(_('Mixed purchase and sale moves'))
        elif fields.first(self).is_purchase_document():
            return super()._post(soft)

        invoice_ids = self.browse()
        correction_ids = self.browse()

        for move_id in self:
            # update x_invoice_sale_date if not set
            if move_id.move_type != 'entry' and not move_id.x_invoice_sale_date:
                if not move_id.invoice_date:
                    if move_id.is_sale_document(include_receipts=True):
                        move_id.x_invoice_sale_date = fields.Date.context_today(move_id)

                    elif move_id.is_purchase_document(include_receipts=True):
                        raise UserError(_('The Bill/Refund date is required to validate this document.'))

                else:
                    move_id.x_invoice_sale_date = move_id.invoice_date

            if (
                move_id.move_type == 'out_refund'
                and move_id.currency_id.compare_amounts(move_id.amount_total, 0.0) < 0
            ):
                correction_ids |= move_id

            else:
                invoice_ids |= move_id

        return super(AccountMove, invoice_ids)._post(soft) | correction_ids._x_post_wo_validation(soft)

    def _x_post_wo_validation(self, soft=True):
        """Post or validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterward.

        :param soft (bool): If True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :return Model<account.move>: The documents that have been posted
        """
        if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
            raise AccessError(_("You don't have the access rights to post an invoice."))

        # CHANGE TO THE DEFAULT
        if not self.env.context.get('move_reverse_cancel') and self._x_is_installed_stock_account():
            self.env['account.move.line'].create(self._stock_account_prepare_anglo_saxon_out_lines_vals())
        # END CHANGE TO THE DEFAULT

        for move_id in self.filtered(lambda _move: _move.is_invoice(include_receipts=True)):
            if (
                move_id.quick_edit_mode
                and move_id.quick_edit_total_amount
                and move_id.quick_edit_total_amount != move_id.amount_total
            ):
                raise UserError(
                    _(
                        'The current total is %s but the expected total is %s. In order to post the invoice/bill, '
                        'you can adjust its lines or the expected Total (tax inc.).',
                        formatLang(self.env, move_id.amount_total, currency_obj=move_id.currency_id),
                        formatLang(self.env, move_id.quick_edit_total_amount, currency_obj=move_id.currency_id),
                    )
                )
            if move_id.partner_bank_id and not move_id.partner_bank_id.active:
                raise UserError(
                    _(
                        'The recipient bank account linked to this invoice is archived.\n'
                        'So you cannot confirm the invoice.'
                    )
                )
            # CHANGE TO THE DEFAULT
            if (
                move_id.move_type != 'out_refund'
                and float_compare(move_id.amount_total, 0.0, precision_rounding=move_id.currency_id.rounding) < 0
            ):
                raise UserError(
                    _(
                        'You cannot validate an invoice with a negative total amount. '
                        'You should create a credit note instead. '
                        'Use the action menu to transform it into a credit note or refund.'
                    )
                )
            # END CHANGE TO THE DEFAULT

            if not move_id.partner_id:
                if move_id.is_sale_document():
                    raise UserError(
                        _("The field 'Customer' is required, please complete it to validate the Customer Invoice.")
                    )
                elif move_id.is_purchase_document():
                    raise UserError(
                        _("The field 'Vendor' is required, please complete it to validate the Vendor Bill.")
                    )

            # Handle a case when the invoice_date is not set.
            # In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            if not move_id.invoice_date:
                if move_id.is_sale_document(include_receipts=True):
                    move_id.invoice_date = fields.Date.context_today(self)
                elif move_id.is_purchase_document(include_receipts=True):
                    raise UserError(_('The Bill/Refund date is required to validate this document.'))

        if soft:
            future_move_ids = self.filtered(lambda _move: _move.date > fields.Date.context_today(self))
            for move_id in future_move_ids:
                if move_id.auto_post == 'no':
                    move_id.auto_post = 'at_date'
                msg = _(
                    'This move will be posted at the accounting date: %(date)s',
                    date=format_date(self.env, move_id.date),
                )
                move_id.message_post(body=msg)
            to_post_ids = self - future_move_ids
        else:
            to_post_ids = self

        for move_id in to_post_ids:
            if move_id.state == 'posted':
                raise UserError(_('The entry %s (id %s) is already posted.') % (move_id.name, move_id.id))

            if not move_id.line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_note')):
                raise UserError(_('You need to add a line before posting.'))

            if move_id.auto_post != 'no' and move_id.date > fields.Date.context_today(self):
                date_msg = move_id.date.strftime(get_lang(self.env).date_format)
                raise UserError(_('This move is configured to be auto-posted on %s', date_msg))

            if not move_id.journal_id.active:
                raise UserError(
                    _(
                        'You cannot post an entry in an archived journal (%(journal)s)',
                        journal=move_id.journal_id.display_name,
                    )
                )

            if move_id.display_inactive_currency_warning:
                raise UserError(
                    _('You cannot validate a document with an inactive currency: %s', move_id.currency_id.name)
                )

            if move_id.line_ids.account_id.filtered(lambda account: account.deprecated):
                raise UserError(_('A line of this move is using a deprecated account, you cannot post it.'))

            affects_tax_report = move_id._affect_tax_report()
            lock_dates = move_id._get_violated_lock_dates(move_id.date, affects_tax_report)

            if lock_dates:
                move_id.date = move_id._get_accounting_date(move_id.invoice_date or move_id.date, affects_tax_report)

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        to_post_ids.line_ids._create_analytic_lines()

        # Trigger copying for recurring invoices
        to_post_ids.filtered(lambda m: m.auto_post not in ('no', 'at_date'))._copy_recurring_entries()

        for move_id in to_post_ids:
            # Fix inconsistencies that may occur if the OCR has been editing the invoice at the same time of a user.
            # We force the partner on the lines to be the same as the one on the move, because that's the only one the
            # user can see/edit.
            wrong_lines = move_id.is_invoice() and move_id.line_ids.filtered(
                lambda aml: aml.partner_id != move_id.commercial_partner_id
                and aml.display_type not in ('line_note', 'line_section')
            )
            if wrong_lines:
                wrong_lines.write({'partner_id': move_id.commercial_partner_id.id})

        to_post_ids.write({'state': 'posted', 'posted_before': True})

        for move_id in to_post_ids:
            move_id.message_subscribe(
                [p.id for p in [move_id.partner_id] if p not in move_id.sudo().message_partner_ids]
            )

            if (
                move_id.is_sale_document()
                and move_id.journal_id.sale_activity_type_id
                and (move_id.journal_id.sale_activity_user_id or move_id.invoice_user_id).id
                not in (self.env.ref('base.user_root').id, False)
            ):
                move_id.activity_schedule(
                    date_deadline=min(
                        (date for date in move_id.line_ids.mapped('date_maturity') if date), default=move_id.date
                    ),
                    activity_type_id=move_id.journal_id.sale_activity_type_id.id,
                    summary=move_id.journal_id.sale_activity_note,
                    user_id=move_id.journal_id.sale_activity_user_id.id or move_id.invoice_user_id.id,
                )

        customer_count, supplier_count = defaultdict(int), defaultdict(int)
        for move_id in to_post_ids:
            if move_id.is_sale_document():
                customer_count[move_id.partner_id] += 1

            elif move_id.is_purchase_document():
                supplier_count[move_id.partner_id] += 1

        for partner, count in customer_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)

        for partner, count in supplier_count.items():
            (partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

        # Trigger action for paid invoices if the amount is zero
        to_post_ids.filtered(
            lambda m_id: m_id.is_invoice(include_receipts=True) and m_id.currency_id.is_zero(m_id.amount_total)
        )._invoice_paid_hook()

        # CHANGE TO THE DEFAULT
        if (
            not self.env.context.get('skip_cogs_reconciliation')
            and not self.env.context.get('move_reverse_cancel')
            and self._x_is_installed_stock_account()
        ):
            # noinspection PyUnresolvedReferences
            self._stock_account_anglo_saxon_reconcile_valuation()
        # END CHANGE TO THE DEFAULT

        return to_post_ids

    # noinspection PyMethodMayBeStatic
    def _x_format_float(self, number, currency, env):
        return formatLang(env, 0.0 if currency.is_zero(number) else number, currency_obj=currency)

    @api.depends(
        'line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id', 'currency_id'
    )
    def x_get_invoice_amount_summary(self):
        self.ensure_one()

        # Not working on something else than invoices.
        if not self.is_invoice(include_receipts=True):
            return {}

        lang_env = self.with_context(lang=self.partner_id.lang).env
        balance_multiplicator = -1 if self.is_inbound() else 1

        tax_line_ids = self.line_ids.filtered('tax_line_id')
        base_line_ids = self.line_ids.filtered('tax_ids') | self.invoice_line_ids

        tax_group_mapping = defaultdict(
            lambda: {'base_lines': set(), 'base_amount': 0.0, 'tax_amount': 0.0, 'in_local': 0.0}
        )
        # noinspection PyPep8Naming
        EmptyTaxGroup = self.env['account.tax.group']

        # Compute base amounts.
        for base_line_id in base_line_ids:
            base_amount = balance_multiplicator * (
                base_line_id.amount_currency if base_line_id.currency_id else base_line_id.balance
            )

            for tax in base_line_id.tax_ids.flatten_taxes_hierarchy():
                if base_line_id.tax_line_id.tax_group_id == tax.tax_group_id:
                    continue

                tax_group_vals = tax_group_mapping[tax.tax_group_id]
                if base_line_id not in tax_group_vals['base_lines']:
                    tax_group_vals['base_amount'] += base_amount
                    tax_group_vals['base_lines'].add(base_line_id)

            if not base_line_id.tax_ids and base_line_id not in tax_group_mapping[EmptyTaxGroup]['base_lines']:
                tax_group_vals = tax_group_mapping[EmptyTaxGroup]
                tax_group_vals['base_amount'] += base_amount
                tax_group_vals['base_lines'].add(base_line_id)

        # Compute tax amounts.
        for tax_line_id in tax_line_ids:
            tax_amount = balance_multiplicator * (
                tax_line_id.amount_currency if tax_line_id.currency_id else tax_line_id.balance
            )
            tax_group_vals = tax_group_mapping[tax_line_id.tax_line_id.tax_group_id]
            tax_group_vals['tax_amount'] += tax_amount
            tax_group_vals['in_local'] += balance_multiplicator * tax_line_id.balance

        tax_groups = sorted(tax_group_mapping.keys(), key=lambda x: x.sequence)
        amount_by_group = []
        for tax_group in tax_groups:
            tax_group_vals = tax_group_mapping[tax_group]
            # noinspection PyTypeChecker
            amount_by_group.append(
                (
                    tax_group.name,
                    tax_group_vals['tax_amount'],
                    tax_group_vals['base_amount'],
                    formatLang(lang_env, tax_group_vals['tax_amount'], currency_obj=self.currency_id),
                    formatLang(lang_env, tax_group_vals['base_amount'], currency_obj=self.currency_id),
                    len(tax_group_mapping),
                    tax_group.id,
                    formatLang(lang_env, tax_group_vals['in_local'], currency_obj=self.company_currency_id),
                    tax_group_vals['in_local'],
                )
            )

        summary = {'base_amount': 0.0, 'tax_amount': 0.0, 'in_local': 0.0}

        for tax_group_vals in tax_group_mapping.values():
            summary['base_amount'] += tax_group_vals['base_amount']
            summary['tax_amount'] += tax_group_vals['tax_amount']
            summary['in_local'] += tax_group_vals['in_local']

        summary.update(
            {
                'base_amount': summary['base_amount'],
                'tax_amount': summary['tax_amount'],
                'in_local': summary['in_local'],
            }
        )

        return {
            'base': self._x_format_float(summary['base_amount'], self.currency_id, lang_env),
            'base_float': summary['base_amount'],
            'amount': self._x_format_float(summary['tax_amount'], self.currency_id, lang_env),
            'amount_float': summary['tax_amount'],
            'in_local': self._x_format_float(summary['in_local'], self.company_currency_id, lang_env),
            'in_local_float': summary['in_local'],
            'total': self._x_format_float((summary['base_amount'] + summary['tax_amount']), self.currency_id, lang_env),
            'total_float': summary['base_amount'] + summary['tax_amount'],
        }

    def _reverse_moves(self, default_values_list=None, cancel=False):
        if not self.env.company.x_use_ti:
            if self.filtered('x_use_ti'):
                raise UserError(_('Mixed Trilab Invoice enabled and non-enabled moves'))

            return super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)

        from odoo.addons.account.models import account_move

        type_reverse_map_copy = account_move.TYPE_REVERSE_MAP.copy()

        try:
            account_move.TYPE_REVERSE_MAP.update({'out_refund': 'out_refund'})

            result = super()._reverse_moves(default_values_list=default_values_list, cancel=cancel)

            for move_id, default_values in zip(result, default_values_list or []):
                result.partner_bank_id = default_values.get('partner_bank_id', result.partner_bank_id)

        finally:
            account_move.TYPE_REVERSE_MAP = type_reverse_map_copy

        return result

    def action_reverse_pl(self):
        self.ensure_one()

        action = self.env.ref('trilab_invoice.action_view_account_move_reversal_pl').sudo().read()[0]

        if self.is_invoice():
            action['name'] = _('Credit Note PL')

        return action

    def x_num2words(self, amount: float, currency):
        amount = '{:.2f}'.format(amount)
        lang = self.env.context.get('lang', 'en')
        # If template preview
        tmpl_id = self._context.get('default_mail_template_id')
        if tmpl_id:
            template = self.env['mail.template'].browse([tmpl_id])
            if template.lang:
                lang = template._render_lang(self.ids)[self.id]

        try:
            # noinspection PyPackageRequirements
            from num2words import num2words

            # noinspection PyBroadException
            try:
                return num2words(amount, lang=lang, to='currency', currency=currency)

            except NotImplementedError:
                _logger.warning(f'num2words - unsupported language {lang}/{currency}')
                return ''

            except Exception:
                # currency convert unsupported for this language (no proper exception returned)
                return num2words(amount, lang=lang)

        except ImportError:
            _logger.warning('num2words not installed, no text2word for invoice')
            return ''

        except Exception as e:
            _logger.error('num2words - %s', e)
            return ''

    @api.depends('reversed_entry_id')
    def _x_compute_corrected_amount_total(self):
        if not self.env.company.x_use_ti:
            return

        for move_id in self:
            move_id.x_corrected_amount_total = move_id.amount_total + sum(
                move_id.x_corrected_invoice_line_ids.mapped('price_total')
            )

    @api.depends('amount_total', 'amount_residual')
    def _x_compute_amount(self):
        for move_id in self:
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            # noinspection PyProtectedMember
            currencies = move_id._get_lines_onchange_currency().currency_id

            for line_id in move_id.line_ids:
                if move_id.is_invoice(include_receipts=True):
                    if line_id.display_type in ('product', 'line_section', 'line_note'):
                        total += line_id.balance
                        total_currency += line_id.amount_currency

                    elif line_id.tax_line_id:
                        total += line_id.balance
                        total_currency += line_id.amount_currency

                    elif line_id.account_id.account_type in ('asset_receivable', 'liability_payable'):
                        total_residual += line_id.amount_residual
                        total_residual_currency += line_id.amount_residual_currency

                else:
                    if line_id.debit:
                        total += line_id.balance
                        total_currency += line_id.amount_currency

            if move_id.is_purchase_document():
                sign = -1
            else:
                sign = 1

            move_id.x_amount_total = sign * abs(total_currency if len(currencies) == 1 else total)
            move_id.x_amount_residual = total_residual_currency if len(currencies) == 1 else total_residual

    def _x_update_currency_rate(self):
        @lru_cache
        def _get_currency_rate(from_currency, to_currency, company_id, date):
            return self.env['res.currency']._get_conversion_rate(from_currency, to_currency, company_id, date)

        for move_id in self:
            if move_id.currency_id and move_id.currency_id != move_id.company_currency_id:
                move_id.x_currency_rate = _get_currency_rate(
                    move_id.currency_id,
                    move_id.company_currency_id,
                    move_id.company_id,
                    move_id.x_invoice_sale_date
                    or move_id.invoice_date
                    or move_id.date
                    or fields.Date.context_today(move_id),
                )
            else:
                move_id.x_currency_rate = 1.0

    @api.onchange('x_currency_rate', 'invoice_date', 'date')
    def _x_onchange_currency_rate(self):
        # update currency rate if is empty
        if self.x_show_currency_rate and float_is_zero(self.x_currency_rate, precision_digits=4):
            self._x_update_currency_rate()

    @api.onchange('currency_id', 'x_invoice_sale_date')
    def _inverse_currency_id(self):
        # force update currency rate on currency_id & x_invoice_sale_date change
        for move_id in self.filtered(lambda _l: _l.is_invoice(True)):
            move_id.line_ids.currency_id = move_id.currency_id

        update_ids = self.filtered('x_show_currency_rate')
        if update_ids:
            update_ids._x_update_currency_rate()

        super()._inverse_currency_id()

    @api.depends('company_id.x_enable_invoice_rate_change', 'currency_id', 'company_currency_id')
    def _x_compute_show_currency_rate(self):
        for move_id in self:
            move_id.x_show_currency_rate = (
                move_id.x_use_ti
                and move_id.company_id.x_enable_invoice_rate_change
                and move_id.currency_id != move_id.company_currency_id
            )

    def x_is_jpk_mpp(self):
        """Checking whether account_move has field 'x_pl_vat_mpp (extension from 'trilab_jpk_base' module"""
        self.ensure_one()
        return bool(getattr(self, 'x_pl_vat_mpp', False))

    @api.onchange('invoice_date')
    def _x_onchange_invoice_date(self):
        if self.move_type != 'entry' and not self.x_invoice_sale_date:
            self.x_invoice_sale_date = self.invoice_date

    @api.depends('commercial_partner_id', 'move_type')
    def _compute_bank_partner_id(self):
        for move_id in self:
            if move_id.x_use_ti:
                if move_id.is_inbound() or move_id.move_type == 'out_refund':
                    move_id.bank_partner_id = move_id.company_id.partner_id
                else:
                    move_id.bank_partner_id = move_id.commercial_partner_id
            else:
                super(AccountMove, move_id)._compute_bank_partner_id()

    def _preprocess_taxes_map(self, taxes_map):
        # round tax amounts to 2 decimal places, self is a single record
        for tax in taxes_map:
            taxes_map[tax]['amount'] = self.currency_id.round(taxes_map[tax]['amount'])

        return taxes_map

    def x_show_vat_to_local(self, tax_totals=None):
        self.ensure_one()

        if tax_totals is None:
            return self.currency_id != self.company_currency_id

        return (self.currency_id != self.company_currency_id) and (
            not self.company_currency_id.is_zero(tax_totals['x_tax_amount_local'])
        )

    def action_switch_invoice_into_refund_credit_note(self):
        if self._context.get('x_disable_refund_switch'):
            return

        return super().action_switch_invoice_into_refund_credit_note()

    def x_get_related_final_invoices(self):
        self.ensure_one()

        if self.invoice_origin and self.date:
            return self.search(
                [
                    ('invoice_origin', '=', self.invoice_origin),
                    ('state', '=', 'posted'),
                    ('date', '<=', self.date),
                    ('move_type', '=', 'out_invoice'),
                    ('id', '!=', self.id),
                ]
            ).filtered('x_advance_invoices_ids')

        else:
            return self.browse()

    def action_recalculate_advance_payment(self):
        self.ensure_one()

        if self.state != 'draft':
            raise ValidationError(_('Only draft invoice can be recalculated!'))

        if self.invoice_line_ids.filtered(
            lambda l_id: len(l_id.tax_ids) != 1
        ) or self.x_final_source_id.order_line.filtered(lambda l_id: len(l_id.tax_id) != 1 and not l_id.display_type):
            raise ValidationError(_('Multiple or missing taxes for lines'))

        if self.x_final_source_id.order_line.invoice_lines.move_id.filtered(
            lambda move_id: move_id != self and move_id.state == 'draft'
        ):
            raise ValidationError(_('Only one draft invoice can be recalculated!'))

        sum_advances = defaultdict(float)
        for line_id in self.x_final_source_id.order_line.filtered(
            lambda line: line.is_downpayment and not line.display_type
        ):
            sum_advances[line_id.tax_id.id] -= line_id.untaxed_amount_to_invoice

        sum_items = sum(self.invoice_line_ids.filtered(lambda l_id: not l_id.is_downpayment).mapped('price_subtotal'))

        for line_id in self.invoice_line_ids.filtered(
            lambda line: line.is_downpayment
            and line.tax_ids.id in sum_advances
            and not line.currency_id.is_zero(line.price_unit)
        ):
            price_unit = (
                line_id.tax_ids.compute_all(line_id.price_unit, currency=line_id.currency_id)['total_excluded']
                if line_id.tax_ids.price_include
                else line_id.price_unit
            )

            if line_id.currency_id.compare_amounts(sum_items, sum_advances[line_id.tax_ids.id]) == -1:
                qty = sum_items / price_unit
            else:
                qty = sum_advances[line_id.tax_ids.id] / price_unit

            line_id.quantity = -min(
                float_round(
                    qty,
                    precision_digits=self.env['decimal.precision'].precision_get('Product Unit of Measure'),
                    rounding_method='DOWN',
                ),
                1.0,
            )

            sum_items += line_id.price_subtotal
            sum_advances[line_id.tax_ids.id] += line_id.price_subtotal

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        # noinspection PyUnusedLocal
        self = self.with_context(x_ti_additional_checks_eligible_for_cogs=True)
        # noinspection PyUnresolvedReferences
        return super()._stock_account_prepare_anglo_saxon_out_lines_vals()

    def x_get_reversed_invoice_ids(self):
        self.ensure_one()

        reversed_invoice_ids = self.env['account.move']

        invoice_id = self

        while invoice_id.reversed_entry_id:
            reversed_invoice_ids |= invoice_id.reversed_entry_id
            invoice_id = invoice_id.reversed_entry_id

        return reversed_invoice_ids.sorted(reverse=True)

    @api.model
    def _x_is_installed_stock_account(self):
        return self.env['ir.module.module']._get('stock_account').state == 'installed'
    
    def x_is_sale_refund(self):
        return self.is_sale_document() and self.move_type.endswith('_refund')
