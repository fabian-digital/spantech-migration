import base64
import logging

from lxml import etree
from odoo import api, fields, models
from odoo.exceptions import UserError
from unidecode import unidecode

_logger = logging.getLogger(__name__)


class JPKDocument(models.Model):
    _name = 'jpk.document'
    _description = 'JPK Document'

    transfer_id = fields.Many2one('jpk.transfer', required=True, ondelete='cascade')
    transfer_state = fields.Selection(related='transfer_id.state', string='Transfer State')
    document_type_id = fields.Many2one('jpk.document.type', required=True)

    name = fields.Char(related='original_file_id.name', readonly=True)
    active = fields.Boolean(related='transfer_id.active', store=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)
    original_file_id = fields.Many2one('ir.attachment', required=True, string='Original File')
    original_file_id_datas = fields.Binary(
        related='original_file_id.datas', readonly=False, string='Original File Data'
    )
    original_file_id_name = fields.Char(
        related='original_file_id.name', readonly=False, string='Original File Filename'
    )
    iv = fields.Char('Initialization Vector - IV', size=50)
    zip_file_id = fields.Many2one('ir.attachment')
    zip_file_id_datas = fields.Binary(related='zip_file_id.datas')
    zip_file_id_name = fields.Char(related='zip_file_id.name', string='ZIP File Name')

    file_part_ids = fields.One2many('jpk.file.part', 'transfer_document_id')

    is_valid = fields.Boolean(compute='_is_valid_schema', store=True)

    @api.onchange('original_file_id_datas')
    def create_attachment(self):
        if not self.original_file_id and self.original_file_id_datas:
            self.original_file_id = (
                self.env['ir.attachment']
                .create({'name': self.original_file_id_name, 'datas': self.original_file_id_datas})
                .id
            )

    def create_with_attachment(self, data):
        file_name = data.get('file_name')

        file_name = unidecode(file_name).replace(' ', '_')

        attachment_id = self.env['ir.attachment'].create(
            [
                {
                    'name': file_name,
                    'datas': base64.encodebytes(data.get('data')),
                    'res_model': 'jpk.transfer',
                    'res_id': data.get('transfer_id'),
                    'type': 'binary',
                }
            ]
        )

        return self.env['jpk.document'].create(
            [
                {
                    'transfer_id': data.get('transfer_id'),
                    'document_type_id': self.env.ref(data.get('document_type')).id,
                    'name': file_name,
                    'original_file_id': attachment_id.id,
                }
            ]
        )

    def is_valid_schema(self, raise_exceptions=False):
        is_valid = False

        try:
            if not self.document_type_id:
                raise UserError('missing document type')

            if not self.document_type_id.xsd_id_datas:
                raise UserError('missing xml schema')

            if not self.original_file_id.x_full_path:
                raise UserError('missing source xml file')

            xml_document = etree.parse(self.original_file_id.x_full_path)
            xml_validator = etree.XMLSchema(file=self.document_type_id.xsd_id.x_full_path)
            is_valid = xml_validator.validate(xml_document)

            if not is_valid:
                _logger.info(f'Invalid document {self.original_file_id.name}: {xml_validator.error_log}')
                raise UserError(xml_validator.error_log)

        except (UserError, etree.LxmlError, etree.XMLSyntaxError, etree.XMLSchemaParseError) as e:
            _logger.info(f'Error during document validation of {self}: {e}')
            if raise_exceptions:
                raise

        return is_valid

    @api.depends('document_type_id', 'original_file_id_datas')
    def _is_valid_schema(self):
        for document in self:
            document.is_valid = document.is_valid_schema()

    def action_validate_schema(self):
        self.is_valid = self.is_valid_schema(True)
