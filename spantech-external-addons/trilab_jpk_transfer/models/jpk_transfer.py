import ast
import base64
import logging
import os
import tempfile
from pathlib import Path
from urllib.parse import urljoin
from zipfile import ZIP_DEFLATED, ZipFile

import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import padding as asymetric_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from jinja2 import Template
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from zeep import Client as ZClient

_logger = logging.getLogger(__name__)

EDOCUMENTS_API_BASE_URL = 'https://e-mikrofirma.mf.gov.pl/jpk-client-2-api/api/'
EDECLARATIONS_API_BASE_URL = 'https://klient-eformularz.mf.gov.pl/api/'


class JPKTransfer(models.Model):
    _name = 'jpk.transfer'
    _description = 'JPK Transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(tracking=True, required=True)
    color = fields.Integer()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company.id)

    settings_id = fields.Many2one('jpk.settings', required=True)
    jpk_type = fields.Selection(
        [
            ('JPK', 'JPK - documents sent cyclically'),
            ('JPKAH', 'JPKAH - ad-hoc sending of documents during inspection'),
        ],
        default='JPK',
        required=True,
    )

    # Metadane transferu do podpisania
    unsigned_metadata_id = fields.Many2one('ir.attachment', string='Unsigned Metadata')
    unsigned_metadata_id_datas = fields.Binary(related='unsigned_metadata_id.datas', string='Unsigned Metadata Data')
    unsigned_metadata_id_name = fields.Char(related='unsigned_metadata_id.name', string='Unsigned Metadata Filename')

    # podpisane metadane transferu
    signed_metadata_id = fields.Many2one('ir.attachment', string='Signed Metadata')
    signed_metadata_id_datas = fields.Binary(
        related='signed_metadata_id.datas', readonly=False, string='Signed Metadata Data'
    )
    signed_metadata_id_name = fields.Char(
        related='signed_metadata_id.name', readonly=False, string='Signed Metadata Filename'
    )

    initial_response = fields.Char()

    # potwierdzenie transferu
    confirmation_id = fields.Many2one('ir.attachment', string='Confirmation')
    confirmation_id_datas = fields.Binary(related='confirmation_id.datas', string='Confirmation Data')
    confirmation_id_name = fields.Char(related='confirmation_id.name', string='Confirmation Data Filename')

    secret_key = fields.Char()
    error_description = fields.Text(tracking=True)
    reference_number = fields.Char(tracking=True)
    reference_document = fields.Reference(selection=[('jpk.vat.7m', 'V7M'), ('jpk.vat.ue', 'VAT UE')])
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('to_sign', 'To Sign'),
            ('sent', 'Sent to IRS'),
            ('confirmed', 'Confirmed'),
            ('declined', 'Declined'),
        ],
        default='draft',
        required=True,
        readonly=True,
        group_expand='get_all_stages',
        tracking=True,
    )
    document_ids = fields.One2many('jpk.document', 'transfer_id')
    last_description = fields.Char()

    def create_with_document(self, data):
        rec = {'state': 'draft'}

        for k, v in data.items():
            # noinspection PyUnresolvedReferences
            if k in self._fields:
                rec[k] = v

        rec.setdefault('company_id', self.env.company.id)

        transfer_id = self.create(rec)
        data['transfer_id'] = transfer_id.id
        document_id = self.env['jpk.document'].create_with_attachment(data)

        settings_id = self.sudo().settings_id.search(
            [('gate_type', '=', document_id.document_type_id.gate_type), ('name', 'ilike', 'prod')], limit=1
        )

        if settings_id:
            transfer_id.settings_id = settings_id

        return transfer_id

    def unlink(self):
        if any(transfer_id.state != 'declined' for transfer_id in self):
            raise ValidationError(_('You can only delete declined JPK Transfers.'))

        return super().unlink()

    @api.constrains('active')
    def constrains_active(self):
        if any(
            transfer_id.state not in ('confirmed', 'declined')
            for transfer_id in self.with_context(active_test=False).filtered(lambda transfer: not transfer.active)
        ):
            raise ValidationError(_('You can only archive confirmed and declined JPK Transfers.'))

    @api.onchange('signed_metadata_id_datas')
    def create_attachment(self):
        if not self.signed_metadata_id and self.signed_metadata_id_datas:
            self.signed_metadata_id = (
                self.env['ir.attachment']
                .create({'name': self.signed_metadata_id_name, 'datas': self.signed_metadata_id_datas})
                .id
            )

    # noinspection PyUnusedLocal
    @api.model
    def get_all_stages(self, stages, domain, order):
        # pełna lista stanów w widoku kanban
        return [key for key, val in JPKTransfer.state.selection]

    def validate_transfer(self):
        self.ensure_one()

        if (names := self.document_ids.mapped('name')) and len(set(names)) != len(names):
            raise ValidationError(_('Selected files do not have unique file names!'))

        for document_id in self.document_ids:
            if len(document_id.name) < self.settings_id.jpk_min_filename_length:
                raise ValidationError(
                    _(
                        'File %s has too short name, minimum is %d',
                        document_id.name,
                        self.settings_id.jpk_min_filename_length,
                    )
                )

            if len(document_id.name) > self.settings_id.jpk_max_filename_length:
                raise ValidationError(
                    _(
                        'File %s has too long name, maximum is %d',
                        document_id.name,
                        self.settings_id.jpk_max_filename_length,
                    )
                )

    def _get_gate_method_callable(self, method_name_suffix):
        """
        Get the `self` method for setting gate_type with the provided method name suffix.
        Searchable method syntax: _{gate_type}_{method_name_suffix}
        """
        self.ensure_one()

        settings_id = self.sudo().settings_id

        f = getattr(self, f'_{settings_id.gate_type.lower()}_{method_name_suffix}', None)

        if f is None:
            raise ValidationError(
                _('Method `%s` has not been implemented for: %s', method_name_suffix, settings_id.display_name)
            )

        return f

    def _edocuments_create_transfer_request(self):
        self.validate_transfer()

        settings_id = self.sudo().settings_id
        backend = default_backend()
        encryption_key = os.urandom(settings_id.jpk_encryption_file_key_size)
        self.secret_key = base64.b64encode(encryption_key)

        for document_id in self.document_ids:
            # hash sha256 base64 original_file_id
            origin_file_read = open(document_id.original_file_id.x_full_path, 'rb').read()

            digest = hashes.Hash(hashes.SHA256(), backend=backend)
            digest.update(origin_file_read)
            document_id.original_file_id.x_jpk_hash = base64.b64encode(digest.finalize())

            encryption_iv = os.urandom(settings_id.jpk_encryption_file_iv_size)
            document_id.iv = base64.b64encode(encryption_iv)

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir = Path(tmp_dir)
                zip_file_name = f'{document_id.name[:43]}.zip'
                zip_file_path = tmp_dir / zip_file_name

                with ZipFile(zip_file_path, 'w', ZIP_DEFLATED) as zipfile:
                    zipfile.write(document_id.original_file_id.x_full_path, document_id.name)

                document_id.zip_file_id = self.env['ir.attachment'].create(
                    {
                        'datas': base64.encodebytes(open(zip_file_path, 'rb').read()),
                        'name': zip_file_name,
                        'res_model': 'jpk.document',
                        'res_id': document_id.id,
                    }
                )

                file_part = 0
                data_copied = 0
                output_file = None
                output_file_name = None
                input_file = open(document_id.zip_file_id.x_full_path, 'rb')
                cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(encryption_iv), backend=backend)
                encryptor = None
                padder = None
                digest = None

                while True:
                    data = input_file.read(64 * 1024)

                    if data:
                        if output_file is None:
                            file_part += 1
                            encryptor = cipher.encryptor()
                            padder = padding.PKCS7(settings_id.jpk_encryption_file_block_size * 8).padder()
                            digest = hashes.Hash(hashes.MD5(), backend=backend)
                            output_file_name = f'{zip_file_name}.{file_part:03d}.aes'
                            output_file = open(tmp_dir / output_file_name, 'w+b')

                        encrypted_data = encryptor.update(padder.update(data))
                        output_file.write(encrypted_data)
                        digest.update(encrypted_data)
                        data_copied += len(data)

                    if data_copied >= settings_id.jpk_max_chunk_size or (not data and output_file):
                        data = encryptor.update(padder.finalize()) + encryptor.finalize()
                        output_file.write(data)
                        output_file.seek(0)

                        digest.update(data)

                        file_part_obj = self.env['ir.attachment'].create(
                            {
                                'datas': base64.encodebytes(output_file.read()),
                                'name': output_file_name,
                                'type': 'binary',
                                'res_model': 'jpk.file.part',
                                'x_jpk_hash': base64.b64encode(digest.finalize()),
                            }
                        )

                        self.env['jpk.file.part'].create(
                            {
                                'transfer_document_id': document_id.id,
                                'file_part_id': file_part_obj.id,
                                'part_number': file_part,
                            }
                        )
                        output_file = None
                        data_copied = 0

                    if not data:
                        break

                input_file.close()
                self.state = 'to_sign'

        key = Path(settings_id.jpk_mf_public_key_id.x_full_path).read_bytes()
        certificate = x509.load_pem_x509_certificate(key, backend=backend)
        public_key = certificate.public_key()
        encryption_key = base64.b64encode(public_key.encrypt(encryption_key, asymetric_padding.PKCS1v15()))

        template = Template((Path(__file__).parent / 'templates/InitUpload').read_text())
        unsigned_metadata = template.render(transfer=self, encryption_key=encryption_key.decode('utf-8'))

        self.unsigned_metadata_id = (
            self.env['ir.attachment']
            .create(
                {
                    'datas': base64.b64encode(unsigned_metadata.encode('utf-8')),
                    'name': 'unsigned_metadata.xml',
                    'type': 'binary',
                    'res_model': 'jpk.transfer',
                    'res_id': self.id,
                }
            )
            .id
        )

    def _edeclarations_create_transfer_request(self):
        self.ensure_one()

        if len(self.document_ids) != 1:
            raise ValidationError(
                _('It is not allowed to use e-Declarations API Gate to send multiple documents at once.')
            )

        if Path(self.document_ids.name).suffix != '.xml':
            raise ValidationError(_('It is not allowed to use e-Declarations API Gate to send non XML documents.'))

        self.unsigned_metadata_id = self.document_ids.original_file_id

        self.state = 'to_sign'

    def create_transfer_request(self):
        self.ensure_one()

        if self.state != 'draft':
            return

        return self._get_gate_method_callable('create_transfer_request')()

    def _edocuments_send_initial_request(self):
        response = requests.post(
            f'{self.settings_id.endpoint_url}/api/Storage/InitUploadSigned',
            data=Path(self.signed_metadata_id.x_full_path).read_bytes(),
            headers={'Content-Type': 'application/xml'},
        )

        if response.ok:
            data = response.json()
            file_part_dict = {}

            self.initial_response = response.text
            self.reference_number = data.get('ReferenceNumber')

            for data_slice in data.get('RequestToUploadFileList'):
                file_part_dict[data_slice.get('FileName')] = data_slice

            for document_id in self.document_ids:
                for file_part_id in document_id.file_part_ids:
                    file_part_id.cloud_meta = file_part_dict[file_part_id.name]
                    file_part_id.blob_name = file_part_dict[file_part_id.name].get('BlobName')
                    self.upload_file_part(file_part_id)

            self.state = 'sent'

        else:
            raise ValidationError(response.text)

    def _edeclarations_send_initial_request(self):
        self.ensure_one()

        settings = self.sudo().settings_id

        client = ZClient(settings.endpoint_url)

        response = getattr(client.service, 'sendDocument')(document=self.signed_metadata_id.raw)

        self.initial_response = str(response)
        self.reference_number = getattr(response, 'refId', None)

        self.state = 'sent'

    def send_initial_request(self):
        if self.state != 'to_sign':
            return

        return self._get_gate_method_callable('send_initial_request')()

    def check_transfer_completeness(self):
        if all(part.uploaded for part in self.document_ids.file_part_ids):
            self.send_final_request()

    def upload_file_part(self, file_part_id):
        if file_part_id.cloud_meta:
            headers = {}
            cloud_meta = ast.literal_eval(file_part_id.cloud_meta)

            for header in cloud_meta['HeaderList']:
                headers[header['Key']] = header['Value']

            response = requests.put(
                cloud_meta['Url'], data=Path(file_part_id.file_part_id.x_full_path).read_bytes(), headers=headers
            )

            if response.ok:
                file_part_id.uploaded = True
                self.check_transfer_completeness()

            else:
                raise Exception(f'Error uploading file: {response.text}')

        else:
            raise Exception('Missing CloudMeta')

    def send_final_request(self):
        request = {'ReferenceNumber': self.reference_number, 'AzureBlobNameList': []}
        for document_id in self.document_ids:
            for file_part_id in document_id.file_part_ids:
                request['AzureBlobNameList'].append(file_part_id.blob_name)

        response = requests.post(f'{self.settings_id.endpoint_url}/api/Storage/FinishUpload', json=request)

        if response.ok:
            self.get_request_status()

        else:
            raise ValidationError(response.text)

    def _edocuments_get_request_status(self):
        response = requests.get(f'{self.settings_id.endpoint_url}/api/Storage/Status/{self.reference_number}')

        if response.ok:
            data = response.json()
            _logger.debug(f'_edocuments_get_request_status: {data}')

            if self.last_description != data.get('Description'):
                self.message_post(body=_('Check request status: %s', data.get('Description')))
                self.last_description = data.get('Description')

            code = data.get('Code')
            if code == 200:
                if data.get('Upo'):
                    confirmation_att = self.env['ir.attachment'].create(
                        {
                            'name': 'confirmation.xml',
                            'datas': base64.b64encode(data.get('Upo').encode('UTF-8')),
                            'res_model': 'jpk.transfer',
                            'res_id': self.id,
                        }
                    )
                    self.confirmation_id = confirmation_att.id
                    self.state = 'confirmed'

            elif code > 400:
                self.message_post(body=_('Check request status: [%s] %s', code, data.get('Description')))
                self.state = 'declined'

            else:
                self.state = 'sent'

        else:
            self.error_description = response.text
            self.state = 'declined'

    def _edeclarations_get_request_status(self):
        self.ensure_one()

        if not self.reference_number:
            return

        client = ZClient(self.sudo().settings_id.endpoint_url)

        response = getattr(client.service, 'requestUPO')(refId=self.reference_number)

        status_code = getattr(response, 'status', None)
        status_desc = getattr(response, 'statusOpis', None)

        _logger.debug(f'_edeclarations_get_request_status: [{status_code}] {status_desc}')

        if status_code == 200:
            if getattr(response, 'upo'):
                confirmation_att = self.env['ir.attachment'].create(
                    {
                        'name': 'confirmation.xml',
                        'datas': base64.b64encode(response.upo.encode('UTF-8')),
                        'res_model': 'jpk.transfer',
                        'res_id': self.id,
                    }
                )
                self.confirmation_id = confirmation_att.id
                self.state = 'confirmed'

        elif 300 < status_code < 400:
            self.state = 'sent'

        else:
            self.message_post(body=_('Check request status: [%s] %s', status_code, status_desc))
            self.state = 'declined'

    def get_request_status(self):
        if self.state != 'sent':
            return

        return self._get_gate_method_callable('get_request_status')()

    def move_to_declined(self):
        if self.state in ('draft', 'to_sign'):
            self.state = 'declined'

    @api.model
    def check_transfer_status_cron(self):
        for transfer_id in self.search([('state', '=', 'sent')]):
            transfer_id.get_request_status()

    def _edeclarations_get_confirmation_pdf_url(self):
        return urljoin(EDECLARATIONS_API_BASE_URL, f'upo/{self.reference_number}/pdf')

    def _edocuments_get_confirmation_pdf_url(self):
        return urljoin(EDOCUMENTS_API_BASE_URL, f'upo/pdf/{self.reference_number}')

    def action_get_confirmation_pdf(self):
        self.ensure_one()

        if not self.reference_number or self.state != 'confirmed':
            return

        return {
            'type': 'ir.actions.act_url',
            'name': 'Confirmation Download Page',
            'target': 'new',
            'url': self._get_gate_method_callable('get_confirmation_pdf_url')(),
        }
