from flask import Flask, render_template, request
import xmlrpc.client
import os
from dotenv import load_dotenv

# carga las variables de entorno desde el archivo .env
load_dotenv()

ODOO_URL = os.getenv('ODOO_URL')
ODOO_DB = os.getenv('ODOO_DB')
ODOO_USERNAME = os.getenv('ODOO_USERNAME')
# usa la clave api en lugar de la contraseña para la autenticación
ODOO_API_KEY = os.getenv('ODOO_API_KEY')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # reemplazar con una clave secreta segura en producción

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None

    if request.method == 'POST':
        try:
            # conecta al endpoint común para obtener información de la versión del servidor
            common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
            version = common.version()

            # autentica usando la clave api como contraseña
            uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, {})
            if not uid:
                error = "Authentication failed."
            else:
                # conecta al endpoint de objetos para operaciones adicionales
                models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

                # obtiene los campos especificados de los leads
                lead_fields = [
                    'id', 'campaign_id', 'source_id', 'medium_id', 'message_bounce',
                    'user_id', 'team_id', 'company_id', 'stage_id', 'color',
                    'recurring_plan', 'partner_id', 'title', 'lang_id', 'state_id',
                    'country_id', 'lost_reason_id', 'create_uid', 'write_uid',
                    'phone_sanitized', 'email_normalized', 'email_cc', 'name',
                    'referred', 'type', 'priority', 'contact_name', 'partner_name',
                    'function', 'email_from', 'email_domain_criterion', 'phone',
                    'mobile', 'phone_state', 'email_state', 'website', 'street',
                    'street2', 'zip', 'city', 'date_deadline', 'lead_properties',
                    'description', 'expected_revenue', 'prorated_revenue',
                    'recurring_revenue', 'recurring_revenue_monthly',
                    'recurring_revenue_monthly_prorated', 'recurring_revenue_prorated',
                    'active', 'date_closed', 'date_automation_last', 'date_open',
                    'date_last_stage_update', 'date_conversion', 'create_date',
                    'write_date', 'day_open', 'day_close', 'probability',
                    'automated_probability', 'reveal_id', 'iap_enrich_done',
                    'lead_mining_request_id'
                ]

                # busca los leads
                lead_ids = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'crm.lead', 'search',
                    [[]],
                    {'limit': 10}  # limita a 10 leads para demostración
                )

                # lee los datos de los leads
                leads = models.execute_kw(
                    ODOO_DB, uid, ODOO_API_KEY,
                    'crm.lead', 'read',
                    [lead_ids],
                    {'fields': lead_fields}
                )

                result = {
                    'version': version,
                    'uid': uid,
                    'leads': leads
                }
        except Exception as e:
            error = str(e)

    return render_template('index.html', result=result, error=error)

if __name__ == '__main__':
    app.run(debug=True)
