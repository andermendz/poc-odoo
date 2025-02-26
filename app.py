from flask import Flask, render_template, request, redirect, url_for, flash
import xmlrpc.client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ODOO_URL = os.getenv('ODOO_URL')
ODOO_DB = os.getenv('ODOO_DB')
ODOO_USERNAME = os.getenv('ODOO_USERNAME')
ODOO_API_KEY = os.getenv('ODOO_API_KEY')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key in production

# Define common lead fields
LEAD_FIELDS = [
    'id', 'name', 'contact_name', 'partner_name', 'email_from', 'phone',
    'expected_revenue', 'probability', 'stage_id', 'user_id', 'team_id',
    'description'
]

def connect_to_odoo():
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_API_KEY, {})
    if not uid:
        raise Exception("Authentication failed")
    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    return uid, models

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        uid, models = connect_to_odoo()
        
        # Get all stages for filtering
        stages = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'crm.stage', 'search_read',
            [[]], {'fields': ['id', 'name']})
        
        # Handle search and filtering
        domain = []
        search_query = request.args.get('search', '')
        if search_query:
            domain.append('|')
            domain.append(('name', 'ilike', search_query))
            domain.append(('contact_name', 'ilike', search_query))
        
        stage_id = request.args.get('stage')
        if stage_id and stage_id.isdigit():
            domain.append(('stage_id', '=', int(stage_id)))
        
        # Get leads
        leads = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'crm.lead', 'search_read',
            [domain],
            {'fields': LEAD_FIELDS, 'limit': 50})
        
        return render_template('index.html',
            leads=leads,
            stages=stages,
            search_query=search_query,
            current_stage=stage_id)
            
    except Exception as e:
        flash(str(e), 'error')
        return render_template('index.html', leads=[], stages=[])

@app.route('/lead/new', methods=['GET', 'POST'])
def new_lead():
    if request.method == 'POST':
        try:
            uid, models = connect_to_odoo()
            
            # Create new lead
            lead_data = {
                'name': request.form['name'],
                'contact_name': request.form['contact_name'],
                'partner_name': request.form['partner_name'],
                'email_from': request.form['email'],
                'phone': request.form['phone'],
                'expected_revenue': float(request.form['expected_revenue'] or 0),
                'probability': float(request.form['probability'] or 0),
                'description': request.form['description']
            }
            
            lead_id = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
                'crm.lead', 'create',
                [lead_data])
                
            flash('Lead created successfully!', 'success')
            return redirect(url_for('view_lead', lead_id=lead_id))
            
        except Exception as e:
            flash(str(e), 'error')
            return render_template('new_lead.html')
            
    return render_template('new_lead.html')

@app.route('/lead/<int:lead_id>')
def view_lead(lead_id):
    try:
        uid, models = connect_to_odoo()
        
        # Get lead details
        leads = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'crm.lead', 'read',
            [lead_id],
            {'fields': LEAD_FIELDS})
            
        if not leads:
            flash('Lead not found', 'error')
            return redirect(url_for('index'))
            
        return render_template('view_lead.html', lead=leads[0])
        
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))

@app.route('/lead/<int:lead_id>/edit', methods=['GET', 'POST'])
def edit_lead(lead_id):
    try:
        uid, models = connect_to_odoo()
        
        if request.method == 'POST':
            # Update lead
            lead_data = {
                'name': request.form['name'],
                'contact_name': request.form['contact_name'],
                'partner_name': request.form['partner_name'],
                'email_from': request.form['email'],
                'phone': request.form['phone'],
                'expected_revenue': float(request.form['expected_revenue'] or 0),
                'probability': float(request.form['probability'] or 0),
                'description': request.form['description']
            }
            
            models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
                'crm.lead', 'write',
                [[lead_id], lead_data])
                
            flash('Lead updated successfully!', 'success')
            return redirect(url_for('view_lead', lead_id=lead_id))
        
        # Get lead details for form
        leads = models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'crm.lead', 'read',
            [lead_id],
            {'fields': LEAD_FIELDS})
            
        if not leads:
            flash('Lead not found', 'error')
            return redirect(url_for('index'))
            
        return render_template('edit_lead.html', lead=leads[0])
        
    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('index'))

@app.route('/lead/<int:lead_id>/delete', methods=['POST'])
def delete_lead(lead_id):
    try:
        uid, models = connect_to_odoo()
        
        # Delete lead
        models.execute_kw(ODOO_DB, uid, ODOO_API_KEY,
            'crm.lead', 'unlink',
            [[lead_id]])
            
        flash('Lead deleted successfully!', 'success')
        
    except Exception as e:
        flash(str(e), 'error')
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
