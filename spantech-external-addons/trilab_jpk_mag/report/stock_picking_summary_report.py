import datetime

from odoo import _, api, models
from odoo.addons.trilab_jpk_base.models.export_helper import CellDefinition


class StockPickingSummaryReport(models.AbstractModel):
    _name = 'report.trilab_jpk_mag.stock_picking_summary_report'
    _inherit = 'jpk.trilab.export_helper'
    _description = 'Stock Picking Summary Report'

    title_columns = [
        CellDefinition(None, _('Reference'), style='title'),
        CellDefinition(None, _('Date done'), style='title'),
        CellDefinition(None, _('Picking date'), style='title'),
        CellDefinition(None, _('Src Location'), style='title'),
        CellDefinition(None, _('Dest Location'), style='title'),
        CellDefinition(None, _('Contact/Partner name'), style='title'),
        CellDefinition(None, _('Source document'), style='title'),
        CellDefinition(None, _('Related document'), style='title'),
        CellDefinition(None, _('Document Amount'), style='title'),
        CellDefinition(None, _('Backorder'), style='title'),
        CellDefinition(None, _('State'), style='title'),
        CellDefinition(None, _('PO Value'), style='title'),
        CellDefinition(None, _('Landed Costs'), style='title'),
        CellDefinition(None, _('Total Value'), style='title'),
    ]

    @api.model
    def _get_report_name(self):
        return _('Picking Summary')

    def generate_xlsx_report(self, workbook, doc_ids, options):
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        y_offset = 0

        for col_idx, cell_def in enumerate(self.title_columns):
            self._write_cell(sheet, y_offset, col_idx, cell_def.name, definition=cell_def)

        sheet.set_column(0, len(self.title_columns) - 1, 15)

        y_offset += 1

        translated_states = dict(self.env['stock.picking']._fields['state']._description_selection(self.env))
        svl_amount_total = 0
        lc_amount_total = 0
        svl_lc_amount_total = 0

        for picking in self.env['stock.picking'].browse(doc_ids):
            related = [
                *picking.sale_id.invoice_ids.mapped('display_name'),
                *picking.purchase_id.invoice_ids.mapped('display_name'),
            ]

            svl_ids = self.env['stock.valuation.layer']
            for move in picking.move_ids.filtered(lambda m: m not in svl_ids.stock_move_id):
                svl_ids |= move.stock_valuation_layer_ids[-1:]

            doc_amount = sum(svl_ids.mapped('value'))

            # If dropshipped
            if picking.location_id.usage == 'supplier' and picking.location_dest_id.usage == 'customer':
                doc_amount = sum(svl_ids.mapped(lambda l: abs(l.value)))

            svl_ids = picking.move_ids.stock_valuation_layer_ids
            lc_svl_ids = svl_ids.filtered('stock_landed_cost_id')
            svl_ids -= lc_svl_ids
            svl_amount = sum(svl_ids.mapped(lambda _l: abs(_l.value)))
            lc_amount = sum(lc_svl_ids.mapped(lambda _l: abs(_l.value)))
            lc_amount_total += lc_amount
            svl_amount_total += svl_amount
            svl_lc_amount_total += lc_amount + svl_amount

            values = (
                picking.display_name,
                picking.date_done,
                picking.date,
                picking.location_id.display_name,
                picking.location_dest_id.display_name,
                picking.partner_id.display_name,
                picking.origin,
                ', '.join(filter(None, related)),
                doc_amount,
                picking.backorder_id.display_name,
                translated_states[picking.state],
                svl_amount,
                lc_amount,
                lc_amount + svl_amount,
            )

            for col_idx, val in enumerate(values):
                style = 'default'
                if isinstance(val, datetime.date):
                    style = f'{style}_date'
                self._write_cell(sheet, y_offset, col_idx, val, style=style)

            y_offset += 1

            self._write_cell(sheet, y_offset, 11, svl_amount_total)
            self._write_cell(sheet, y_offset, 12, lc_amount_total)
            self._write_cell(sheet, y_offset, 13, svl_lc_amount_total)
