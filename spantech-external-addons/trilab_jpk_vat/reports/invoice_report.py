from odoo import _, api, models
from odoo.addons.trilab_jpk_base.models.export_helper import CellDefinition


class InvoiceReport(models.AbstractModel):
    _name = 'report.trilab_jpk_vat.invoice_report'
    _inherit = ['jpk.trilab.export_helper']
    _description = 'Invoice Report'

    # noinspection PyArgumentList
    columns = [
        CellDefinition('name', _('Number')),
        CellDefinition('partner_name', _('Partner Name')),
        CellDefinition('invoice_date', _('Invoice Date'), 'date'),
        CellDefinition('sale_data', _('Sale Date'), 'date'),
        CellDefinition('vat_date', _('Vat Date'), 'date'),
        CellDefinition('address', _('Address')),
        CellDefinition('city', _('City')),
        CellDefinition('zip_code', _('Code')),
        CellDefinition('vat', _('NIP')),
        CellDefinition('fp', _('Fiscal Position')),
        CellDefinition('origin', _('Origin')),
        CellDefinition('salesperson', _('Salesperson')),
        CellDefinition('company', _('Company')),
        CellDefinition('due_date', _('Date Due'), 'date'),
        CellDefinition('state', _('State')),
        CellDefinition('refunded', _('Correction Invoice Number')),
        CellDefinition('partner_id', _('Partner ID')),
        CellDefinition('currency', _('Currency')),
        CellDefinition('total', _('Total Net in base currency'), 'float', 'monetary'),
    ]

    tax_columns = []

    extra_columns = [
        CellDefinition('refunded', _('Total Gross in base currency'), 'float', 'monetary'),
        CellDefinition('partner_id', _('Total Gross in Currency'), 'float', 'monetary'),
    ]

    # xlsx_styles = {
    #     'default': {'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666'},
    #     'title': {'font_name': 'Arial', 'bold': True, 'bottom': 2},
    # }

    @staticmethod
    def _x_prepare_tax_columns(invoice, tax_groups):
        tax_groups = {group: 0 for group in tax_groups}
        sign = -1 if invoice.is_purchase_document() else 1

        for subtotal in invoice.tax_totals['subtotals']:
            for group in invoice.tax_totals['groups_by_subtotal'][subtotal['name']]:
                tax_groups[group['tax_group_name']] = group['x_tax_group_amount_local'] * sign

        return list(tax_groups.values())

    @api.model
    def _get_report_data(self, docids, options):
        # headers
        table_rows = [[cell.name for cell in self.columns] + ['tmp-taxes'] + [cell.name for cell in self.extra_columns]]

        translated_states = dict(self.env['account.move']._fields['state']._description_selection(self.env))
        tax_groups = set()

        for invoice in self.env['account.move'].browse(docids):
            sign = -1 if invoice.is_purchase_document() else 1

            invoice_tax_groups = {}

            for subtotal in invoice.tax_totals['subtotals']:
                for group in invoice.tax_totals['groups_by_subtotal'][subtotal['name']]:
                    invoice_tax_groups[group['tax_group_name']] = group['x_tax_group_amount_local'] * sign
                    tax_groups.add(group['tax_group_name'])

            table_rows.append(
                [
                    invoice.name,
                    invoice.partner_id.name,
                    invoice.invoice_date,
                    invoice.x_invoice_sale_date,
                    invoice.pl_vat_date,
                    f"{invoice.partner_id.street or ''} {invoice.partner_id.street2 or ''}".strip(),
                    invoice.partner_id.city,
                    invoice.partner_id.zip,
                    invoice.partner_id.vat,
                    invoice.fiscal_position_id.name,
                    invoice.invoice_origin,
                    invoice.sudo().invoice_user_id.name,
                    invoice.company_id.name,
                    invoice.invoice_date_due or invoice.invoice_date,
                    translated_states[invoice.state],
                    invoice.reversed_entry_id.name or '',
                    invoice.partner_id.id,
                    invoice.currency_id.name,
                    abs(invoice.amount_untaxed_signed) * sign,
                    invoice_tax_groups,
                    abs(invoice.amount_total_signed) * sign,
                    abs(invoice.amount_total) * sign,
                ]
            )

        # expand taxes
        tax_groups = sorted(tax_groups)

        for y, row in enumerate(table_rows):
            new_row = row[:19]
            reminder = row[20:]

            if y == 0:
                new_row += [name for name in tax_groups]

            else:
                new_row += [row[19].get(name) for name in tax_groups]

            new_row += reminder

            table_rows[y] = new_row

        return table_rows

    @api.model
    def _get_report_name(self):
        return _('Invoice Report')

    def generate_xlsx_report(self, workbook, doc_ids, options):
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        # Iterate over worksheet_data by columns and set max column width
        max_widths = []
        columns = []

        for y, row in enumerate(self._get_report_data(doc_ids, options)):
            if not columns:
                columns = self.columns + [
                    CellDefinition(name, name, 'float', 'monetary') for name in row[len(self.columns) :]
                ]

            if not max_widths:
                max_widths = [0] * len(row)

            for x, value in enumerate(row):
                self._write_cell(sheet, y, x, value, definition=columns[x] if x < len(columns) else None)
                max_widths[x] = max(max_widths[x], len(str(value)))

        for x, width in enumerate(max_widths):
            sheet.set_column(x, x, width + 10)
