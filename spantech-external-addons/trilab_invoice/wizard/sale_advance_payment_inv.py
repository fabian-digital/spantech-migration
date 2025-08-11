from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    x_invoice_line_ids = fields.Many2many('sale.order.line', compute='_x_compute_invoice_line_ids')
    x_company_currency_id = fields.Many2one('res.currency', compute='_x_compute_invoice_line_ids')

    x_advance_lines = fields.One2many('trilab.sale.advance.line', 'wizard_id', string='Advance Lines')
    x_advance_payment_method_2 = fields.Selection(
        [('normal', 'Normal Invoice'), ('advance', 'Advance Invoice')],
        default='normal',
        required=1,
        string='Invoice Type',
    )
    x_journal_id = fields.Many2one('account.journal', string='Sale Journal')
    x_convert_to_local = fields.Boolean(string='Convert To Local Currency')
    x_convert_rate = fields.Many2one('res.currency.rate', string='Convert Rate')
    x_orders_currency_id = fields.Many2one(
        'res.currency', string='Orders Currency', compute='_x_compute_orders_currency_id'
    )
    x_is_convertible = fields.Boolean(string='Is Convertible', compute='_x_compute_orders_currency_id')
    x_partner_bank_id = fields.Many2one('res.partner.bank', string='Account Number')
    x_allowed_partner_bank_ids = fields.Many2many(
        'res.partner.bank', compute='_x_compute_allowed_partner_bank_accounts'
    )

    @api.onchange('x_advance_payment_method_2')
    def _x_onchange_advance_payment_method_2(self):
        if self.env.company.x_use_ti:
            if self.x_advance_payment_method_2 == 'normal':
                self.advance_payment_method = 'delivered'
            else:
                self.advance_payment_method = 'fixed'

    @api.depends('sale_order_ids.order_line')
    def _x_compute_invoice_line_ids(self):
        for wizard_id in self:
            wizard_id.x_invoice_line_ids = [
                fields.Command.set(
                    wizard_id.sale_order_ids.order_line.filtered(lambda l_id: l_id.invoice_status == 'to invoice').ids
                )
            ]
            wizard_id.x_company_currency_id = self.env.company.currency_id

    @api.depends('sale_order_ids', 'sale_order_ids.currency_id')
    def _x_compute_orders_currency_id(self):
        for wizard_id in self:
            if not wizard_id.sale_order_ids:
                raise ValidationError(_('Missing sale order'))

            currency_ids = wizard_id.sale_order_ids.currency_id

            wizard_id.x_is_convertible = (
                len(currency_ids) == 1
                and currency_ids != wizard_id.x_company_currency_id
                and all(
                    currency_id == wizard_id.x_company_currency_id
                    for currency_id in wizard_id.sale_order_ids.invoice_ids.currency_id
                )
            )

            wizard_id.x_orders_currency_id = fields.first(currency_ids) if wizard_id.x_is_convertible else False

    @api.onchange('x_convert_to_local')
    def _x_onchange_convert_to_local(self):
        if self.x_convert_to_local:
            self.currency_id = self.x_company_currency_id

        else:
            self.x_convert_rate = False

    @api.onchange('x_allowed_partner_bank_ids')
    def _x_onchange_set_partner_bank_account(self):
        self.ensure_one()
        self.x_partner_bank_id = self.x_allowed_partner_bank_ids._origin[:1]

    @api.depends('sale_order_ids.currency_id', 'sale_order_ids.company_id', 'x_convert_to_local')
    def _x_compute_allowed_partner_bank_accounts(self):
        for wizard in self:
            currency_id = (
                wizard.x_company_currency_id if wizard.x_convert_to_local else wizard.sale_order_ids[:1].currency_id
            )

            wizard.x_allowed_partner_bank_ids = self.env['res.partner.bank'].search(
                [
                    ('partner_id', '=', fields.first(wizard.sale_order_ids).company_id.partner_id.id),
                    ('currency_id', '=', currency_id.id),
                ]
            )

    @api.onchange('advance_payment_method')
    def _onchange_advance_payment_method(self):
        if not self.env.company.x_use_ti:
            return super()._onchange_advance_payment_method()

        if len(self.sale_order_ids) == 1:
            advance_lines = [fields.Command.clear()]
            tax_ids = self.env['account.tax'].browse(self.sale_order_ids.order_line.mapped('tax_id').ids)
            for tax_id in tax_ids:
                line_ids = self.sale_order_ids.order_line.filtered(lambda lne: lne.tax_id.ids == [tax_id.id])
                currency_id = self.currency_id or self.x_company_currency_id
                subtotal = currency_id.round(sum(line.price_subtotal for line in line_ids))

                advance_lines.append(
                    fields.Command.create(
                        {
                            'tax_id': tax_id.id,
                            'original_subtotal': subtotal,
                            'original_total': currency_id.round(subtotal * (1.0 + (tax_id.amount / 100.0))),
                            'currency_id': currency_id.id,
                        }
                    )
                )

            self.x_advance_lines = advance_lines

    def _prepare_invoice_values(self, order, so_line):
        if not self.env.company.x_use_ti:
            return super()._prepare_invoice_values(order, so_line)

        invoice_vals = None

        for line_id in so_line:
            values = super()._prepare_invoice_values(order, line_id)

            if invoice_vals:
                invoice_vals['invoice_line_ids'].extend(values['invoice_line_ids'])

            else:
                invoice_vals = values

        if not invoice_vals.get('x_invoice_sale_date'):
            invoice_vals['x_invoice_sale_date'] = fields.Date.context_today(order)

        invoice_vals.update({'partner_bank_id': self.x_partner_bank_id.id})

        if self.x_convert_to_local:
            invoice_vals['currency_id'] = self.x_company_currency_id.id

        return invoice_vals

    # def _create_invoice(self, order, so_line, amount):
    #     if not self.env.company.x_use_ti:
    #         return super()._create_invoice(order, so_line, amount)
    #
    #
    #
    #     amount, name = self._get_advance_details(order)
    #     invoice_vals = self._prepare_invoice_values(order, so_line)
    #     if self.x_convert_rate:
    #         invoice_vals['narration'] = _(
    #             'Rate %s with effective date: %s', self.x_convert_rate.inverse_company_rate, self.x_convert_rate.name
    #         )
    #     if order.fiscal_position_id:
    #         invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
    #
    #     # check if we should update currency rate
    #     ctx = {}
    #     if (
    #         order.company_id.x_enable_invoice_rate_change
    #         and order.pricelist_id.currency_id != order.company_id.currency_id
    #     ):
    #         rate = self.env['res.currency']._get_conversion_rate(
    #             order.pricelist_id.currency_id,
    #             order.company_id.currency_id,
    #             order.company_id,
    #             invoice_vals.get('x_invoice_sale_date')
    #             or invoice_vals.get('invoice_date')
    #             or invoice_vals.get('date')
    #             or fields.Date.context_today(self),
    #         )
    #         if not order.company_id.currency_id.is_zero(rate):
    #             ctx['x_trilab_force_currency_rate'] = rate
    #
    #     invoice = self.env['account.move'].sudo().with_context(**ctx).create(invoice_vals).with_user(self.env.uid)
    #
    #     order.check_advance_invoice_values()
    #     invoice.message_post_with_view(
    #         'mail.message_origin_link',
    #         values={'self': invoice, 'origin': order},
    #         subtype_id=self.env.ref('mail.mt_note').id,
    #     )
    #     return invoice

    def _prepare_down_payment_product_values(self):
        output = super()._prepare_down_payment_product_values()

        if self.env.company.x_use_ti:
            output['name'] = _('Advance payment')

            if 'categ_id' not in output:
                output['categ_id'] = self.env.ref('product.product_category_all').id

        return output

    # def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount):
    #     so_values = super()._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
    #
    #     if self.env.company.x_use_ti:
    #         so_values['name'] = _('Advance payment [%s]', self.env['account.tax'].browse(tax_ids[0]).description)
    #
    #     return so_values

    def _prepare_so_line_values(self, order):
        if not self.env.company.x_use_ti:
            return super()._prepare_so_line_values(order)

        self.ensure_one()
        analytic_distribution = {}
        amount_total = sum(order.order_line.mapped('price_total'))

        if not float_is_zero(amount_total, precision_rounding=self.currency_id.rounding):
            for line_id in order.order_line:
                for account, distribution in (line_id.analytic_distribution or {}).items():
                    analytic_distribution[account] = distribution * line_id.price_total + analytic_distribution.get(
                        account, 0
                    )

            for account, distribution_amount in analytic_distribution.items():
                analytic_distribution[account] = distribution_amount / amount_total

        # noinspection PyUnusedLocal
        context = {'lang': order.partner_id.lang}

        # TODO shall we check here for self.x_advance_payment_method_2 == 'advance' ?
        so_values = [
            {
                'name': _('Advance payment [%s]', line_id.tax_id.description),
                'price_unit': line_id.value,
                'product_uom_qty': 0.0,
                'order_id': order.id,
                'discount': 0.0,
                'product_id': self.product_id.id,
                'analytic_distribution': analytic_distribution,
                'is_downpayment': True,
                'sequence': order.order_line and order.order_line[-1].sequence + line_idx or 10,
                'tax_id': [fields.Command.set(line_id.tax_id.ids)],
            }
            for line_idx, line_id in enumerate(self.x_advance_lines, 1)
        ]

        del context
        return so_values

    def _create_invoices(self, sale_orders):
        if not self.env.company.x_use_ti:
            return super()._create_invoices(sale_orders=sale_orders)

        self.ensure_one()

        self = self.with_context(
            {
                **self.env.context,
                'x_advance': True,  # mark that this is advance wizard
                'invoice_type': self.advance_payment_method,
                'x_journal_id': self.x_journal_id.id,
                'x_convert_rate': self.x_convert_rate.id,
                'x_partner_bank_id': self.x_partner_bank_id.id,
            }
        ).with_company(self.company_id)

        # limit line selection only for orders with downpayments
        if self.has_down_payments and self.advance_payment_method not in ('fixed', 'percentage'):
            self = self.with_context(selected_invoice_lines=self.x_invoice_line_ids.ids)

        sale_orders = sale_orders.with_context(self._context)

        if self.x_advance_payment_method_2 == 'normal':
            if not self.x_invoice_line_ids.filtered(
                lambda invoice_line: not invoice_line.is_downpayment and not invoice_line.display_type
            ):
                raise ValidationError(_('There are no order lines that are delivered to be invoiced.'))

        if self.advance_payment_method == 'delivered':
            return sale_orders._create_invoices(final=self.deduct_down_payments)

        else:
            return super()._create_invoices(sale_orders=sale_orders)

    def _check_amount_is_positive(self):
        # supress constraint for PL companies
        if not self.env.company.x_use_ti:
            super()._check_amount_is_positive()


class SaleAdvanceLine(models.TransientModel):
    _name = 'trilab.sale.advance.line'
    _description = 'Sale Advance Line'

    wizard_id = fields.Many2one('sale.advance.payment.inv', required=1)
    tax_id = fields.Many2one('account.tax', required=1)
    original_subtotal = fields.Monetary()
    original_total = fields.Monetary()
    value = fields.Monetary(required=0, string='Value [NET]')
    value_total = fields.Monetary(required=0, string='Value [GROSS]')
    percent = fields.Float(required=0, string='Value Percent')
    currency_id = fields.Many2one('res.currency')

    @api.constrains('value', 'percent')
    def constrains_values(self):
        for line_id in self:
            if line_id.wizard_id.advance_payment_method == 'delivered':
                continue

            if line_id.percent < 0:
                raise UserError(_('Percent Value must be positive'))

            if line_id.percent > 100:
                raise UserError(_('Percent Value cannot be greater than 100%'))

            total = line_id.original_total if line_id.tax_id.price_include else line_id.original_subtotal

            if line_id.percent:
                line_id.write({'value': total * (line_id.percent / 100), 'percent': 0})

            if line_id.value < 0:
                raise UserError(_('Advance line value must be positive'))

            # rounding issue #4245
            if line_id.value - total > 0.05:
                raise UserError(_('Advance line value is bigger than order value'))

    @api.onchange('value')
    def onchange_value(self):
        if 'value' not in self.env.context:
            return

        self.write(
            {
                'value_total': self.value * (1.0 + (self.tax_id.amount / 100.0)),
                'percent': (self.value / self.original_subtotal) * 100.0,
            }
        )

    @api.onchange('value_total')
    def onchange_value_total(self):
        if 'value_total' not in self.env.context:
            return

        value = self.value_total / (1 + (self.tax_id.amount / 100.0))
        percent = (value / self.original_subtotal) * 100.0

        self.write({'value': value, 'percent': percent})

    @api.onchange('percent')
    def onchange_percent(self):
        if 'percent' not in self.env.context:
            return

        value = self.currency_id.round(self.original_subtotal * (self.percent / 100.0))
        value_total = self.currency_id.round(value * (1.0 + (self.tax_id.amount / 100.0)))

        self.write({'value': value, 'value_total': value_total})
