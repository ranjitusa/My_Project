from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import datetime

app = Flask(__name__)
DATABASE = 'tax_database.db'

def create_table():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS payments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  company TEXT,
                  amount REAL,
                  payment_date TEXT,
                  status TEXT,
                  due_date TEXT,
                  tax_rate REAL)''')
    # Create indexes
    c.execute('''CREATE INDEX IF NOT EXISTS idx_company ON payments (company)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_payment_date ON payments (payment_date)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_due_date ON payments (due_date)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_status ON payments (status)''')
    c.execute('''CREATE INDEX IF NOT EXISTS idx_tax_rate ON payments (tax_rate)''')
    conn.commit()
    conn.close()

create_table()



create_table()
def format_date_mmddyyyy(date_str):
    if date_str:  
        parts = date_str.split('-') 
        if len(parts) == 3:
            return f"{parts[1]}/{parts[2]}/{parts[0]}"  
    return date_str  

@app.route('/submit', methods=['POST'])
def submit():
    company = request.form['company']
    amount = float(request.form['amount'])
    payment_date = request.form['paymentDate']
    status = request.form['status']
    due_date = request.form['dueDate']
    tax_rate = float(request.form['taxRate'])

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO payments (company, amount, payment_date, status, due_date, tax_rate)
                 VALUES (?, ?, ?, ?, ?, ?)''', (company, amount, payment_date, status, due_date, tax_rate))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/')
def index():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    current_year = datetime.datetime.now().year
    next_year = current_year + 1
    due_dates = [
        f"04/15/{current_year}",
        f"06/15/{current_year}",
        f"09/15/{current_year}",
        f"01/15/{next_year}"
    ]
    c.execute('''SELECT * FROM payments''')
    records = c.fetchall()
    return render_template('index.html',due_dates=due_dates,records=records)

@app.template_filter('format_date')
def format_date(value):
    if value:
        return datetime.datetime.strptime(value, '%Y-%m-%d').strftime('%m/%d/%Y')
    return ''

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d'):
    if isinstance(value, datetime.datetime):
        return value.strftime(format)
    else:
        return value  

@app.route('/insert', methods=['POST'])
def insert_record():
    data = request.get_json()
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''INSERT INTO payments (company, amount, payment_date, status, due_date, tax_rate)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (data['company'], data['amount'], data['payment_date'],
               data['status'], data['due_date'], data['tax_rate']))
    conn.commit()
    conn.close()
    return 'Record inserted successfully'

@app.route('/summary')
def summary():
    due_date = request.args.get('dueDate')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT * FROM payments WHERE due_date=?''', (due_date,))
    data = c.fetchall()
    total_amount = sum(row[2] for row in data)
    
    # Retrieve tax rate and format it as percentage
    tax_rate = data[0][6] * 100 if data else 0
    tax_due = total_amount * (tax_rate / 100)  # Calculate tax due based on percentage
    
    conn.close()

    html = '<table border="1"><tr><th>ID</th><th>Company</th><th>Amount</th><th>Payment Dates</th><th>Status</th><th>Due Date</th></tr>'
    for row in data:
        payment_date = row[3] if row[3] else 'NA'  
        formatted_date = format_date_mmddyyyy(payment_date)  
        html += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{formatted_date}</td><td>{row[4]}</td><td>{row[5]}</td>'
        html += '</td></tr>'
    html += f'<tr><td colspan="5"><strong>Total Amount:</strong></td><td>&dollar;{total_amount}</td></tr><tr><td colspan="5"><strong>Tax Rate:</strong></td><td>{tax_rate}%</td></tr><tr><td colspan="5"><strong>Tax Due:</strong></td><td>&dollar;{tax_due}</td></tr>'
    html += '</table>'

    return jsonify({'html': html})



@app.route('/update', methods=['POST'])
def update():
    edit_id = request.form['editId']
    company = request.form['editCompany']
    amount = float(request.form['editAmount'])
    payment_date = request.form['editPaymentDate']
    status = request.form['editStatus']
    due_date = request.form['editDueDate']
    tax_rate = float(request.form['editTaxRate'])

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''UPDATE payments SET company=?, amount=?, payment_date=?, status=?, due_date=?, tax_rate=? WHERE id=?''',
              (company, amount, payment_date, status, due_date, tax_rate, edit_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/delete', methods=['DELETE'])
def delete():
    delete_id = request.args.get('id')

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''DELETE FROM payments WHERE id=?''', (delete_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
