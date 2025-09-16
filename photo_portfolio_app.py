from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'your_password'  # Change this
app.config['MYSQL_DB'] = 'photography_portfolio'

# Upload Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

mysql = MySQL(app)

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/uploads/gallery', exist_ok=True)
os.makedirs('static/uploads/packages', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database initialization
def init_db():
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Create packages table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS packages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2),
                duration VARCHAR(50),
                features TEXT,
                image_url VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create gallery table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS gallery (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100),
                category VARCHAR(50),
                image_url VARCHAR(255) NOT NULL,
                description TEXT,
                featured BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create services table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(100) NOT NULL,
                description TEXT,
                icon VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create testimonials table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS testimonials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                client_name VARCHAR(100) NOT NULL,
                content TEXT NOT NULL,
                rating INT DEFAULT 5,
                event_type VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create contact inquiries table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS inquiries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                package_interested VARCHAR(100),
                event_date DATE,
                message TEXT,
                status VARCHAR(20) DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create admin users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        mysql.connection.commit()
        
        # Insert sample data if tables are empty
        cur.execute("SELECT COUNT(*) FROM packages")
        if cur.fetchone()[0] == 0:
            # Sample packages
            sample_packages = [
                ('Basic Package', 'Perfect for small events and portrait sessions', 299.00, '2 Hours', 
                 '- 50 edited photos\n- Online gallery\n- Print release\n- 1 location', None),
                ('Premium Package', 'Ideal for weddings and large events', 1299.00, 'Full Day', 
                 '- 200+ edited photos\n- Online gallery\n- USB with all photos\n- 2 photographers\n- Album included', None),
                ('Deluxe Package', 'Complete coverage with video', 2499.00, 'Full Day + Video', 
                 '- Unlimited photos\n- 4K video highlights\n- Drone footage\n- 3 photographers\n- Premium album\n- Same-day preview', None)
            ]
            for pkg in sample_packages:
                cur.execute('''INSERT INTO packages (name, description, price, duration, features, image_url) 
                              VALUES (%s, %s, %s, %s, %s, %s)''', pkg)
            
            # Sample services
            sample_services = [
                ('Wedding Photography', 'Capturing your special day with artistic excellence', 'camera'),
                ('Portrait Sessions', 'Professional portraits for individuals and families', 'user'),
                ('Event Coverage', 'Corporate events, parties, and celebrations', 'calendar'),
                ('Product Photography', 'High-quality product shots for your business', 'package'),
                ('Real Estate', 'Showcase properties with stunning visuals', 'home'),
                ('Photo Editing', 'Professional retouching and enhancement', 'edit')
            ]
            for svc in sample_services:
                cur.execute('''INSERT INTO services (title, description, icon) 
                              VALUES (%s, %s, %s)''', svc)
            
            # Sample testimonials
            sample_testimonials = [
                ('Sarah Johnson', 'Amazing work! The photos from our wedding are absolutely stunning. Professional and creative!', 5, 'Wedding'),
                ('Mike Chen', 'Great experience from start to finish. Highly recommend for any event!', 5, 'Corporate Event'),
                ('Emily Davis', 'The portrait session was fun and the results exceeded our expectations!', 5, 'Portrait')
            ]
            for test in sample_testimonials:
                cur.execute('''INSERT INTO testimonials (client_name, content, rating, event_type) 
                              VALUES (%s, %s, %s, %s)''', test)
            
            # Create default admin user (username: admin, password: admin123)
            cur.execute('''INSERT INTO admin_users (username, password_hash) 
                          VALUES (%s, %s)''', ('admin', generate_password_hash('admin123')))
            
            mysql.connection.commit()
        
        cur.close()

# Routes
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    
    # Get featured gallery images
    cur.execute("SELECT * FROM gallery WHERE featured = TRUE LIMIT 6")
    featured_photos = cur.fetchall()
    
    # Get services
    cur.execute("SELECT * FROM services LIMIT 6")
    services = cur.fetchall()
    
    # Get testimonials
    cur.execute("SELECT * FROM testimonials ORDER BY created_at DESC LIMIT 3")
    testimonials = cur.fetchall()
    
    cur.close()
    
    return render_template('index.html', 
                         featured_photos=featured_photos,
                         services=services,
                         testimonials=testimonials)

@app.route('/packages')
def packages():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM packages ORDER BY price")
    packages = cur.fetchall()
    cur.close()
    return render_template('packages.html', packages=packages)

@app.route('/gallery')
def gallery():
    category = request.args.get('category', 'all')
    cur = mysql.connection.cursor()
    
    if category == 'all':
        cur.execute("SELECT * FROM gallery ORDER BY created_at DESC")
    else:
        cur.execute("SELECT * FROM gallery WHERE category = %s ORDER BY created_at DESC", (category,))
    
    photos = cur.fetchall()
    
    # Get unique categories
    cur.execute("SELECT DISTINCT category FROM gallery WHERE category IS NOT NULL")
    categories = [row[0] for row in cur.fetchall()]
    
    cur.close()
    return render_template('gallery.html', photos=photos, categories=categories, current_category=category)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        package = request.form.get('package')
        event_date = request.form.get('event_date')
        message = request.form.get('message')
        
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO inquiries (name, email, phone, package_interested, event_date, message) 
                      VALUES (%s, %s, %s, %s, %s, %s)''',
                   (name, email, phone, package, event_date if event_date else None, message))
        mysql.connection.commit()
        cur.close()
        
        flash('Thank you for your inquiry! We will contact you soon.', 'success')
        return redirect(url_for('contact'))
    
    # Get packages for dropdown
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, name FROM packages")
    packages = cur.fetchall()
    cur.close()
    
    return render_template('contact.html', packages=packages)

@app.route('/admin')
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, password_hash FROM admin_users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    
    if user and check_password_hash(user[1], password):
        session['admin_logged_in'] = True
        session['admin_id'] = user[0]
        return redirect(url_for('admin_dashboard'))
    
    flash('Invalid credentials', 'error')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    cur = mysql.connection.cursor()
    
    # Get statistics
    cur.execute("SELECT COUNT(*) FROM inquiries WHERE status = 'new'")
    new_inquiries = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM packages")
    total_packages = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM gallery")
    total_photos = cur.fetchone()[0]
    
    # Get recent inquiries
    cur.execute("SELECT * FROM inquiries ORDER BY created_at DESC LIMIT 5")
    recent_inquiries = cur.fetchall()
    
    cur.close()
    
    return render_template('admin_dashboard.html',
                         new_inquiries=new_inquiries,
                         total_packages=total_packages,
                         total_photos=total_photos,
                         recent_inquiries=recent_inquiries)

@app.route('/admin/gallery/add', methods=['POST'])
def admin_add_photo():
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if 'photo' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['photo']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join('static/uploads/gallery', filename)
        file.save(filepath)
        
        title = request.form.get('title')
        category = request.form.get('category')
        description = request.form.get('description')
        featured = request.form.get('featured') == 'true'
        
        cur = mysql.connection.cursor()
        cur.execute('''INSERT INTO gallery (title, category, image_url, description, featured) 
                      VALUES (%s, %s, %s, %s, %s)''',
                   (title, category, f'/static/uploads/gallery/{filename}', description, featured))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'success': True, 'message': 'Photo uploaded successfully'})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, port=8000)