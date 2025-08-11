"""Trilab mBank CompanyConnectWSService Connector"""
import hashlib
import logging
import re
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7, pkcs12
from jinja2 import Environment, FileSystemLoader
from lxml import etree
from requests import Session
from zeep import Client, Plugin, Settings, Transport
from zeep.exceptions import Fault

from odoo.modules import get_resource_path

from .mt940 import MT940

__all__ = ['MBankRequest', 'MBankStatementStatus', 'MBankAuthMethods', 'MBankLanguages', 'MBankApiException']

_logger = logging.getLogger(__name__)

# noinspection HttpUrlsUsage
TNS = 'http://model.ws.hp.com'

WSDL_FILENAME = 'IBREService_v1_0.wsdl'
SERVICE_VERSION = '1.0.9'
TEST_ENDPOINT_URL = 'https://www.companynet-test.ebre.pl/ws/services/IBREService_v1_0'
PROD_ENDPOINT_URL = 'https://ws.companynet.mbank.pl/mt/services/IBREService_v1_0'

STRING_SANITIZE_RE = re.compile(r'[^\w/?:\-().,\'+]+', flags=re.UNICODE | re.MULTILINE | re.DOTALL)

NUMBER_OF_TRIES = 20


class LogPlugin(Plugin):
    """Small plugin for zeep that catches out/ingoing XML requests and logs them"""

    def ingress(self, envelope, http_headers, operation):
        _logger.info(f'mbank_request: {etree.tostring(envelope, pretty_print=True).decode()}')
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        _logger.info(f'mbank_response: {etree.tostring(envelope, pretty_print=True).decode()}')
        return envelope, http_headers


class MBankStatementStatus:
    """Statements Statuses"""

    PENDING = 'PENDING'

    TO_EDIT = 'TO_EDIT'
    TO_AUTH = 'TO_AUTH'
    IN_AUTH = 'IN_AUTH'
    AUTHORIZED = 'AUTHORIZED'
    IN_REALIZ = 'IN_REALIZ'
    REALIZED = 'REALIZED'
    DENIED = 'DENIED'
    PROCESSED = 'PROCESSED'
    CONDITIONAL = 'CONDITIONAL'
    REALIZ_AND_COND = 'REALIZ_AND_COND'
    SIGN_VERIFY = 'SIGN_VERIFY'
    REALIZ = 'REALIZ'
    CONFIRMED = 'CONFIRMED'
    STOPPED = 'STOPPED'
    STOP_CUST_C = 'STOP_CUST_C'
    STOP_ACC_C = 'STOP_ACC_C'
    VALIDATED = 'VALIDATED'
    DELETED = 'DELETED'


class MBankAuthMethods(Enum):
    SIGNATURE = 'sign'
    MOBILE = 'mobile'
    TOKEN = 'token'
    BACKGROUND_SESSION = 'background_session'


class MBankLanguages(Enum):
    POLISH = 'pl'
    ENGLISH = 'en'
    GERMAN = 'de'


class MBankApiException(Exception):
    pass


def _sanitize_string(string: Optional[str], normalize: bool = False) -> str:
    sanitized = STRING_SANITIZE_RE.sub(' ', string or '')
    if normalize:
        sanitized = unicodedata.normalize('NFD', sanitized).encode('ascii', 'ignore').decode()
    return sanitized


@dataclass
class Transaction:
    unique_id: int
    amount: float
    partner_name: str
    partner_acc_num: str
    description: str
    acc_number: str
    currency_code: str
    country: str
    street_name: str
    post_code: str
    city: str
    address: str
    exec_date: Optional[date] = None
    split_payment_data: Optional[dict] = None
    reference: Optional[str] = None

    title: str = field(init=False)
    sanitized_reference: str = field(init=False)
    sanitized_partner_name: str = field(init=False)
    sanitized_address: str = field(init=False)
    sanitized_address_lines: tuple[str, ...] = field(init=False)

    def __post_init__(self):
        self.sanitized_reference = _sanitize_string(self.reference)[:40]
        self.sanitized_partner_name = _sanitize_string(self.partner_name, normalize=True)[:70]
        self.sanitized_address = _sanitize_string(self.address)[:70]
        self.sanitized_address_lines = tuple(filter(None, (self.sanitized_address[:35], self.sanitized_address[35:])))

        if self.split_payment_data:
            amount_str = f"{self.split_payment_data['reconciled_bill_ids'].amount_tax:.2f}".replace('.', ',')
            vat = re.sub(r'\D', '', self.split_payment_data['vat'])
            ref = self.split_payment_data['reconciled_bill_ids'].ref.replace('/', '-')[:35]
            self.title = f"/VAT/{amount_str}/IDC/{vat}/INV/{ref}/TXT/{_sanitize_string(self.description)[:33]}"

        else:
            self.title = _sanitize_string(self.description)[:140]


class MBankRequest:
    test_url = TEST_ENDPOINT_URL
    prod_url = PROD_ENDPOINT_URL
    auth_token = None
    settings = Settings(strict=False)
    client_info = 'Trilab mBank'
    client_version = '2.0'

    def __init__(
        self,
        dik: Union[str, List[str]],
        user_login: str,
        auth_method: MBankAuthMethods,
        is_test: Optional[bool] = False,
        language: Optional[MBankLanguages] = MBankLanguages.ENGLISH,
        enable_logging: bool = False,
    ) -> None:
        if isinstance(dik, str):
            dik = [dik]
        self.dik = dik
        self.wsdl_path = get_resource_path('trilab_mbank', 'wsdl', WSDL_FILENAME)
        self.user_login = user_login
        self.is_test = is_test
        self.language = language
        self.enable_logging = enable_logging
        self.auth_method = auth_method
        self.template_env = Environment(
            loader=FileSystemLoader(get_resource_path('trilab_mbank', 'templates')),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        _logger.debug(
            f'MBankRequest Init dik={dik}, user_login={user_login}, auth_method={auth_method}, is_test={is_test}'
        )

    def _get_client_plugins(self):
        if self.enable_logging:
            return [LogPlugin()]
        return []

    def _call_api(self, method_name: str, logout_after: bool = False, **kwargs) -> Any:
        session = Session()

        if self.is_test:
            session.verify = False

        transport = Transport(session=session)

        client = Client(
            wsdl=self.wsdl_path, settings=self.settings, transport=transport, plugins=self._get_client_plugins()
        )

        client = client.create_service(
            f'{{{TNS}}}IBREService_v1_0HttpBinding', self.test_url if self.is_test else self.prod_url
        )

        try:
            response = getattr(client, method_name)(**kwargs)
            _logger.info(
                f'mBank Api Call method={method_name}, test={self.is_test}, response={response}, kwargs={kwargs}'
            )

            if logout_after:
                _logger.info('mBank Api logout')
                self.logout()

        except Fault as fault:
            _logger.error(
                f'mBank Api Call method={method_name}, fault.code={fault.code}, fault.message={fault.message}'
            )
            raise MBankApiException(f'mBank: {fault.message} ({fault.code})') from fault

        return response

    def import_transactions(self, unique_id: int, transactions: Iterable[dict], company_name, batch_name=None) -> str:
        response = self._import_transactions_raw(unique_id, transactions, company_name, batch_name)

        _logger.info(f'import_transactions unique_id={unique_id} batch_name={batch_name} response={response}')
        return response.groupId

    def _async_call_api(self, task_id: str, method_name: str, sleep_seconds: Optional[float] = 5) -> Any:
        tries = NUMBER_OF_TRIES
        context = {
            'dik': self.dik[0],
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
            'authenticationToken': self.auth_token,
        }
        while tries and task_id:
            response = self._call_api(method_name, context=context, taskId=task_id)
            if response.finished:
                return response
            tries -= 1
            time.sleep(sleep_seconds)

        raise MBankApiException(f'{method_name!r} Ran out of tries. Number of Tries: {NUMBER_OF_TRIES}')

    def _import_transactions_raw(self, unique_id, transactions, company_name, batch_name=None) -> Any:
        context = {
            'dik': self.dik[0],
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
            'authenticationToken': self.auth_token,
        }

        if not batch_name:
            batch_name = f'batch-{unique_id}'
        else:
            batch_name = _sanitize_string(batch_name)[:70]

        data_str = self._get_iso_import_data(unique_id, company_name, transactions)

        metadata = {
            'clientOrderGroupId': unique_id,
            'editable': True,
            'encoding': 'utf8',
            'fileName': f'{batch_name}.xml',
            'format': 'CT_ISO20022',
            'massPayment': False,
            'massPlus': False,
            'massTransfer': False,
            'md5': hashlib.md5(data_str.encode('utf-8')).hexdigest(),
            'modificationDate': datetime.now(),
            'orderAwaitingFunds': False,
            'sendToAuth': False,
        }

        async_task_id = self._call_api(
            'universalPaymentSend',
            context=context,
            orderMetadata=metadata,
            data=data_str,
            validationErrorsAreFatal=False,
        )

        return self._async_call_api(async_task_id, 'checkPaymentSendResult')

    def _get_iso_import_data(self, unique_id: int, company_name: str, transactions: List[dict]) -> str:
        """Render Import Data in CT_ISO20022 format"""
        kwargs = {
            'unique_id': unique_id,
            'now': datetime.now(),
            'company_name': company_name,
            'exec_date': date.today(),
            'acc_number': transactions and transactions[0]['acc_number'],
            'transactions_len': len(transactions),
        }
        return self.template_env.get_template('CT_ISO20022-template.xml').render(
            transactions=[Transaction(**transaction) for transaction in transactions], **kwargs
        )

    def _get_ufp_import_data(self, unique_id: int, transactions: List[dict]) -> str:
        """Render Import Data in UFP format"""
        return self.template_env.get_template('PaymentDocumentList-template.xml').render(
            documents=[
                self._create_payment_document(unique_id, Transaction(**transaction)) for transaction in transactions
            ]
        )

    @staticmethod
    def _create_payment_document(unique_id: int, transaction: Transaction):
        """Prepare document dict for PaymentDocumentList-template.xml"""
        return {
            'payment_id': unique_id,
            # 'payment_type': 'PP' if transaction.split_payment_data else 'Domestic',
            'payment_type': 'Domestic',
            'execution_date': transaction.exec_date,
            'payor_account': transaction.acc_number,
            'transaction_id': transaction.unique_id,
            'amount': transaction.amount,
            'partner_name': transaction.partner_name,
            'street_name': transaction.street_name,
            'post_code': transaction.post_code,
            'city': transaction.city,
            'country': transaction.country,
            'payee_account': transaction.partner_acc_num,
            'ref': transaction.reference or '',
            'title': transaction.description,
            'summary_amount': transaction.amount,
            'transactions_quantity': 1,
        }

    def init_signature_login(self):
        context = {
            'dik': self.dik[0],
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
        }

        return self._call_api('initLoginWithSignature', context=context, userLogin=self.user_login)

    def finish_signature_login(self, signed_token: bytes):
        context = {
            'dik': self.dik[0],
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
        }

        return self._call_api('loginWithSignature', context=context, userLogin=self.user_login, signature=signed_token)

    def _signature_auth(
        self, context: Dict[str, Any], cert_file_path: str, cert_password: Optional[str] = None
    ) -> Tuple[str, bool]:
        token_to_sign = self._call_api('initLoginWithSignature', context=context, userLogin=self.user_login)
        token_to_sign = token_to_sign.encode('utf-16le')

        cert_password = cert_password or ''

        backend = default_backend()
        with open(cert_file_path, 'rb') as file:
            crt_data = file.read()
            private_key, certificate, certificates = pkcs12.load_key_and_certificates(
                crt_data, password=cert_password.encode('utf-8'), backend=backend
            )

        options = [pkcs7.PKCS7Options.DetachedSignature]
        signed = (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(token_to_sign)
            .add_signer(certificate, private_key, hashes.SHA256())
            .sign(serialization.Encoding.PEM, options)
        )

        signed = signed.decode('utf-8')

        # Signature must be in one line without header, UTF-8 encoded
        signed = signed.replace('-----BEGIN PKCS7-----', '')
        signed = signed.replace('\n', '')

        response = self._call_api('loginWithSignature', context=context, userLogin=self.user_login, signature=signed)

        return response.generatedToken, response.confirmationsRequired

    def _token_auth(self, context: Dict[str, Any], token: str) -> Tuple:
        response = self._call_api('login', context=context, userLogin=self.user_login, token=token)
        return response.generatedToken, response.confirmationsRequired

    def init_create_background_session(self, auth_token: str, session_expiration: datetime):
        context = {
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
            'authenticationToken': auth_token,
        }

        return self._call_api(
            'initCreateBackgroundSessionWithSignature',
            context=context,
            permissionConfig=self._get_permission_config(session_expiration),
        )

    def _get_permission_config(self, session_expiration: datetime):
        operations = [
            'getMT940Ex',
            'checkGetMT940Result',
            'getStatus',
            'confirmResponseReceived',
            'universalPaymentSend',
            'checkPaymentSendResult',
        ]

        client = Client(wsdl=self.wsdl_path)
        ArrayOfString = client.get_type('ns1:ArrayOfString')

        return {
            'endTime': session_expiration,
            'permissionsEntries': {
                'BackgroundSessionPermissionEntry': [
                    {'DIK': _d, 'allowedOperations': ArrayOfString(operations)} for _d in self.dik
                ]
            },
        }

    def create_background_session(self, auth_token: str, signed_token: bytes, session_expiration: datetime):
        context = {
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
            'authenticationToken': auth_token,
        }

        return self._call_api(
            'createBackgroundSessionWithSignature',
            context=context,
            signature=signed_token,
            permissionConfig=self._get_permission_config(session_expiration),
        )

    def close_background_session(self, session_token: str):
        self._call_api(
            'finishBackgroundSession',
            context={
                'language': self.language,
                'version': SERVICE_VERSION,
                'clientInfo': self.client_info,
                'clientVersion': self.client_version,
                'authenticationToken': session_token,
            },
        )

    def logout(self):
        self._call_api(
            'logout',
            context={
                'language': self.language,
                'version': SERVICE_VERSION,
                'clientInfo': self.client_info,
                'clientVersion': self.client_version,
                'authenticationToken': self.auth_token,
            },
        )

    def _mobile_auth(self, context) -> Tuple:
        raise NotImplementedError

    def _auth(
        self,
        method: MBankAuthMethods,
        *,
        token: Optional[str] = None,
        cert_file_path: Optional[str] = None,
        cert_password: Optional[str] = None,
        session_token: Optional[str] = None,
    ) -> str:
        context = {
            'dik': self.dik[0],
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
        }

        if method == MBankAuthMethods.SIGNATURE:
            assert cert_file_path, 'Certificate File Path is Required for SIGNATURE Authentication'
            cert_password = cert_password if cert_password is not None else ''
            self.auth_token, self.confirmations_required = self._signature_auth(context, cert_file_path, cert_password)
        elif method == MBankAuthMethods.TOKEN:
            token = '12345678' if self.is_test else token
            assert token, 'Token Parameter is Required for TOKEN Authentication'
            self.auth_token, self.confirmations_required = self._token_auth(context, token)
        elif method == MBankAuthMethods.BACKGROUND_SESSION:
            assert session_token, 'Session Token Parameter is Required for BACKGROUND_SESSION Authentication'
            self.auth_token, self.confirmations_required = session_token, False
        else:
            self.auth_token, self.confirmations_required = self._mobile_auth(context)

        return self.auth_token

    def auth(
        self,
        token: Optional[str] = None,
        cert_file_path: Optional[str] = None,
        cert_password: Optional[str] = None,
        session_token: Optional[str] = None,
    ) -> str:
        return self._auth(
            self.auth_method,
            token=token,
            cert_file_path=cert_file_path,
            cert_password=cert_password,
            session_token=session_token,
        )

    def get_import_status(self, group_id: str) -> Optional[str]:
        context = {
            'dik': self.dik[0],
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
            'authenticationToken': self.auth_token,
        }

        try:
            response = self._call_api('getStatus', context=context, orderGroupId=group_id)

            return response[0].status.statusKey

        except MBankApiException as err:
            _logger.error(f'import status error for: {group_id} {err}')
            return

    def get_statements(self, from_date: date, to_date: date, bank_acc_num: Union[str, Iterable[str]] = None) -> Dict:
        response = self._get_statements_raw(from_date, to_date)

        accounts_statements = defaultdict(list)

        if not response.reports:
            return accounts_statements

        for report in [MT940(content) for content in [report.content for report in response.reports.Report]]:
            for stmt in report.statements:
                accounts_statements[stmt.account_iban].append(stmt)

        if isinstance(bank_acc_num, str):
            bank_acc_num = [bank_acc_num]

        if bank_acc_num:
            accounts_statements = defaultdict(
                list,
                {
                    account_num: statements
                    for account_num, statements in accounts_statements.items()
                    if account_num in bank_acc_num
                },
            )
        return accounts_statements

    def _get_statements_raw(self, from_date: date, to_date: date) -> Any:
        context = {
            'dik': self.dik[0],
            'language': self.language,
            'version': SERVICE_VERSION,
            'clientInfo': self.client_info,
            'clientVersion': self.client_version,
            'authenticationToken': self.auth_token,
        }

        # kwargs as dict to not override from keyword
        async_task_id = self._call_api(
            'getMT940Ex',
            **{
                'context': context,
                'from': datetime.combine(from_date, datetime.min.time(), tzinfo=timezone.utc),
                'to': datetime.combine(to_date, datetime.min.time(), tzinfo=timezone.utc),
                'compressed': False,
            },
        )

        return self._async_call_api(async_task_id, 'checkGetMT940Result')
