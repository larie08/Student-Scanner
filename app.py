from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3, os
import qrcode
import base64
from io import BytesIO
from datetime import datetime


app = Flask(__name__)
app.secret_key = '!$$tidert'

app.config['UPLOAD_FOLDER'] = "static/images"

def get_db_connection():
    conn = sqlite3.connect('personlist.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_students():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students").fetchall()
    conn.close()
    return students

@app.before_request
def make_session_permanent():
    restricted_routes = ['index', 'edit_student', 'delete_student']
    if 'user_id' not in session and request.endpoint in restricted_routes:
        return redirect(url_for('login'))

@app.after_request
def add_cache_control_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    return response

@app.route('/studentlist', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        idno = request.form.get('idno')
        lastname = request.form.get('lastname')
        firstname = request.form.get('firstname')
        course = request.form.get('course')
        level = request.form.get('level')
        photo = request.form.get('photo')

        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(idno)
        qr.make(fit=True)
        buffer = BytesIO()
        qr.img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO students (idno, lastname, firstname, course, level, photo, qr) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (idno, lastname, firstname, course, level, photo, qr_base64)
        )
        conn.commit()
        conn.close()

        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    students = get_students()
    return render_template('index.html', students=students, pagetitle="STUDENT INFORMATION")

@app.route('/generate_qrcode', methods=['POST'])
def generate_qrcode():
    data = request.json.get('idno')
    qr = qrcode.QRCode(box_size=5, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    qrcode_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return jsonify({'qrcode': qrcode_base64})

def generate_and_save_qr(idno):
    folder_path = r"C:\Users\sheka\OneDrive\Desktop\camera\static\images"
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, f"{idno}_qr.png")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(idno)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img.save(file_path)

    return file_path
    
@app.route('/add_student_page', methods=['GET', 'POST'])
def add_student_page():
    if request.method == 'POST':
        idno = request.form['idno']
        lastname = request.form['lastname']
        firstname = request.form['firstname']
        course = request.form['course']
        level = request.form['level']
        photo_data = request.form['photo'] 
        
        if photo_data:
            photo_data = photo_data.split(',')[1]  
            photo_filename = f"{idno}_photo.jpg"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)

            with open(photo_path, "wb") as photo_file:
                photo_file.write(base64.b64decode(photo_data))
                
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO students (idno, lastname, firstname, course, level, photo)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (idno, lastname, firstname, course, level, photo_path))
            conn.commit()
            conn.close()

        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('addstudent.html')

@app.route('/edit_student', methods=['POST'])
def edit_student():
    idno = request.form['edit_idno']
    lastname = request.form['lastname']
    firstname = request.form['firstname']
    course = request.form['course']
    level = request.form['level']
    photo = request.form['edit_photo']
 
    conn = get_db_connection()
    conn.execute('''
        UPDATE students
        SET lastname = ?, firstname = ?, course = ?, level = ?, photo = ?
        WHERE idno = ?
    ''', (lastname, firstname, course, level, photo, idno))
        
    conn.commit()
    conn.close()

    flash('Student details updated successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete/<string:idno>', methods=['POST'])
def delete_student(idno):
    conn = get_db_connection()
    conn.execute("DELETE FROM students WHERE idno = ?", (idno,))
    conn.commit()
    conn.close()
    flash('Student record deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/log_attendance/<idno>', methods=['POST'])
def log_attendance(idno):
    time_logged = datetime.now().strftime('%m/%d/%Y %I:%M %p')

    conn = get_db_connection()
    conn.execute(
        "UPDATE students SET time_logged = ? WHERE idno = ?",
        (time_logged, idno)
    )
    conn.commit()
    conn.close()

    return redirect(url_for('view_attendance'))

@app.route('/attendance')
def view_attendance():
    conn = get_db_connection()
    students = conn.execute("SELECT idno, lastname, firstname, course, level, time_logged FROM students").fetchall()
    conn.close()
    return render_template('attendance.html', students=students)

@app.route('/get_student_details/<idno>', methods=['GET'])
def get_student_details(idno):
    conn = get_db_connection()
    
    student = conn.execute(
        "SELECT idno, lastname, firstname, course, level, photo FROM students WHERE idno = ?",
        (idno,)
    ).fetchone()
    conn.close()

    if student:
        photo_url = f"/static/images/{student['idno']}_photo.jpg"
        return jsonify({
            'idno': student['idno'],
            'lastname': student['lastname'],
            'firstname': student['firstname'],
            'course': student['course'],
            'level': student['level'],
            'photo': photo_url  # Return the path to the image
        })
    else:
        return jsonify({'error': 'Student not found'}), 404
        
@app.route('/')
def scanner():
    return render_template('scanner.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        users = conn.execute("SELECT * FROM USERS WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()
        
        if users:
            session['user_id'] = users['id']
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    # if 'user_id' in session:
    #     session.pop('user_id', None)
    #     flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
