import base64

from jinja2 import Environment, PackageLoader
from lxml import etree, objectify
from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.modules.module import get_resource_path
from odoo.tools import float_repr

env = Environment(
    loader=PackageLoader('odoo.addons.trilab_jpk_fa'), autoescape=True, trim_blocks=True, lstrip_blocks=True
)


class JpkFa4(models.TransientModel):
    _name = 'trilab.jpk.fa'
    _description = 'JPK FA Wizard'

    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    invoice_ids = fields.Many2many('account.move')
    invoice_len = fields.Integer(compute='_compute_invoice_len')
    invoice_line_ids = fields.Many2many('account.move.line', compute='_compute_invoice_line_ids')
    invoice_line_len = fields.Integer(compute='_compute_invoice_line_len')
    jpk_file = fields.Binary(string='JPK File')
    jpk_filename = fields.Char()
    company_id = fields.Many2one('res.company')

    # technical field
    is_jpk_transfer_installed = fields.Boolean(compute='_is_jpk_transfer_installed')

    def _is_jpk_transfer_installed(self):
        """'is_jpk_transfer_installed' determines whether to show export button."""
        self.is_jpk_transfer_installed = self.env.company.x_is_jpk_transfer_installed()

    @api.model
    def default_get(self, fields_list):
        return super().default_get(fields_list) | {
            'invoice_ids': [Command.link(_id) for _id in self.env.context.get('active_ids', [])],
            'company_id': self.env.company.id,
        }

    def generate_jpk(self):
        if not self.company_id.pl_tax_office_id:
            raise ValidationError(_('Please set tax office for current company "%s"', self.company_id.name))

        if not self.company_id.state_id:
            raise ValidationError(_('Please set state for current company "%s"', self.company_id.name))

        if self.invoice_ids.filtered(lambda invoice_id: invoice_id.state != 'posted'):
            raise ValidationError(_('Wrong invoice state - only accepted invoices allowed'))

        if self.invoice_ids.filtered(lambda invoice_id: not invoice_id.is_sale_document()):
            raise ValidationError(_('Wrong invoice type - only sale invoices/corrections allowed'))

        if invalid_move_ids := self.invoice_ids.invoice_line_ids.filtered(
            lambda line_id: line_id.display_type == 'product' and len(line_id.tax_ids) != 1
        ):
            raise ValidationError(
                _(
                    'Invoices containing lines with no tax or multiple taxes: %s',
                    ', '.join(invalid_move_ids.move_id.mapped('name')),
                )
            )

        xml = env.get_template('jpk_fa_template.xml').render(wizard=self).encode()

        try:
            schema = etree.XMLSchema(file=get_resource_path('trilab_jpk_base', 'data', 'Schemat_JPK_FA(4)_v1-0.xsd'))
            parser = objectify.makeparser(schema=schema)
            objectify.fromstring(xml, parser)

        except etree.Error as error:
            raise ValidationError(str(error))

        self.write(
            {
                'state': 'get',
                'jpk_file': base64.b64encode(xml),
                'jpk_filename': f'jpk_fa_{self.get_create_date(False):%Y%m%d_%H%M}.xml',
            }
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'trilab.jpk.fa',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    @api.depends('invoice_ids')
    def _compute_invoice_len(self):
        self.invoice_len = len(self.invoice_ids)

    @api.depends('invoice_ids.invoice_line_ids.display_type')
    def _compute_invoice_line_ids(self):
        self.invoice_line_ids = [
            fields.Command.set(
                self.invoice_ids.invoice_line_ids.filtered(lambda _line: _line.display_type == 'product').ids
            )
        ]

    @api.depends('invoice_line_ids')
    def _compute_invoice_line_len(self):
        self.invoice_line_len = len(self.invoice_line_ids)

    def get_create_date(self, to_str=True):
        value = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return to_str and value.isoformat(timespec='seconds') or value

    def get_date_from(self):
        return min(self.invoice_ids.mapped('invoice_date'))

    def get_date_to(self):
        return max(self.invoice_ids.mapped('invoice_date'))

    # noinspection PyMethodMayBeStatic
    def copy_sign(self, line_id, amt_from, amt_to):
        return abs(amt_to) * line_id.currency_id.compare_amounts(amt_from, 0.0)

    def get_invoice_total_value(self):
        """
        shared method used for 'WartoscFaktur' and 'WartoscWierszyFaktur'
        """
        return float_repr(
            sum(self.invoice_ids.mapped(lambda move_id: move_id.amount_untaxed * -move_id.direction_sign)),
            self.company_id.currency_id.decimal_places,
        )

    def get_value(self, invoice_id, tag_name: str, use_company_currency: bool = False) -> str:
        tag_ids = self.env['account.account.tag'].search(
            [
                ('jpk_account_tag_ids.jpk_markup', '=', tag_name),
                ('jpk_account_tag_ids.jpk_document_type', '=', self.env.ref('trilab_jpk_base.jpk_fa_doc_type').id),
            ]
        )

        return float_repr(
            sum(
                -line_id[use_company_currency and 'balance' or 'amount_currency']
                for line_id in invoice_id.line_ids.filtered(lambda l_id: l_id.tax_tag_ids & tag_ids)
            ),
            precision_digits=invoice_id.currency_id.decimal_places,
        )

    def get_xml(self):
        return base64.b64decode(self.jpk_file)

    # noinspection PyMethodMayBeStatic
    def filter_printable_lines(self, line_ids):
        return line_ids.filtered(lambda line_id: line_id.x_can_print())

    def action_transfer_xml(self):
        if not self.is_jpk_transfer_installed:
            return

        # noinspection PyUnresolvedReferences
        transfer_id = self.env['jpk.transfer'].create_with_document(
            {
                'name': self.jpk_filename.replace('jpk_fa_', 'JPK FA ').rstrip('.xml'),
                'jpk_type': 'JPKAH',
                'file_name': self.jpk_filename,
                'data': self.get_xml(),
                'document_type': 'trilab_jpk_base.jpk_fa_doc_type',
            }
        )

        # noinspection PyUnresolvedReferences
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jpk.transfer',
            'views': [[False, 'form']],
            'res_id': transfer_id.id,
        }
