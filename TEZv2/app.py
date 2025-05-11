from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from functools import wraps

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your_secret_key_here' # Güvenli bir anahtarla değiştirin
app.config['DATABASE'] = 'database.db'

# Veritabanı bağlantısı
def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

# Veritabanı tablolarını oluştur
def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT
            )
        ''')
        # Stocks tablosu için init_db içinde oluşturma daha merkezi olabilir
        db.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                name TEXT, -- Şirket adı için bir alan ekleyebiliriz
                price REAL,
                change REAL,
                volume TEXT, -- Hacim için (örn: "22.78M")
                market_cap TEXT, -- Piyasa değeri için
                rsi REAL, 
                pivot REAL, 
                rel_volume REAL, 
                pe_ratio REAL,
                ev_ebitda REAL,
                dividend_yield REAL,
                volume_15m REAL,
                avg_volume REAL
                -- İhtiyaç duyacağınız diğer alanlar
            )
        ''')
        db.commit()

# Giriş gerektiren sayfalar için decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html') # Ana sayfanız index.html ise

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Geçersiz kullanıcı adı veya şifre')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form.get('email', '')
        
        try:
            db = get_db()
            db.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                       (username, password, email))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Bu kullanıcı adı zaten alınmış')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/screener')
@login_required
def screener():
    return render_template('screener.html')

@app.route('/features')
def features():
    return render_template('features.html')

# create_table fonksiyonu init_db içinde birleştirildiği için ayrıca çağrılmasına gerek kalmayabilir.
# def create_table(): ... Bu fonksiyonu init_db içine taşıdık.
# create_table() çağrısını kaldırabilir veya init_db() içinde olduğundan emin olabilirsiniz.

# === YENİ URL YAPISINA GÖRE GÜNCELLENEN ROUTE ===
@app.route('/hisse/<string:hisse_kodu>')
@login_required # Hisse detay sayfası için de giriş gerekebilir, isteğe bağlı
def stock_detail_page(hisse_kodu):
    # Bu route sadece stock_detail.html şablonunu render eder
    # ve hisse kodunu JavaScript'in kullanması için şablona gönderir.
    # Asıl veri çekme işlemi stock_detail.html'deki JavaScript tarafından
    # /api/hisse_detay/<hisse_kodu> endpoint'i üzerinden yapılacak.
    return render_template('stock_detail.html', symbol_for_js=hisse_kodu)

# === API ENDPOINTS ===

@app.route('/api/stocks_for_screener') # Screener için hisse listesi API'si
@login_required
def get_stocks_for_screener():
    # Bu sizin "dışardan çalıştırdığım bir kodun çıktısını endpoint ile çektiğim hisseler olacak"
    # dediğiniz kısım olabilir. Veritabanından veya başka bir kaynaktan çekilebilir.
    # Şimdilik örnek veriler kullanıyoruz:
    sample_stocks = [
        {"symbol": "GARAN", "price": 320.50, "change": 2.45, "volume": "22.78M", "rsi": 57.8, "pivot": 318.50, "relVolume": 1.82},
        {"symbol": "ASELS", "price": 284.00, "change": 1.89, "volume": "18.45M", "rsi": 53.2, "pivot": 280.75, "relVolume": 1.45},
        {"symbol": "THYAO", "price": 135.75, "change": 3.12, "volume": "30.15M", "rsi": 59.1, "pivot": 132.40, "relVolume": 2.15}
        # Diğer hisseler...
    ]
    # Gerçek uygulamada bu veriyi veritabanınızdan (stocks tablosu) veya harici API'den çekmelisiniz.
    # db = get_db()
    # stocks_data = db.execute('SELECT symbol, price, change, volume, rsi, pivot, rel_volume FROM stocks').fetchall()
    # sample_stocks = [dict(row) for row in stocks_data]
    return jsonify(sample_stocks)

# === HİSSE DETAY VERİLERİ İÇİN YENİ API ENDPOINT'İ ===
@app.route('/api/hisse_detay/<string:hisse_kodu>')
@login_required # Bu endpoint için de giriş gerekebilir
def get_stock_detail_api(hisse_kodu):
    # Bu sizin "bu veriler de dışardan çalışan bir kodun çıktısı olacak ve bu veriler de api endpoint ile gelecek"
    # dediğiniz kısım. Belirli bir hisse için detayları döndürmeli.
    # Veritabanından veya başka bir API'den bu hissenin detaylarını çekin.
    
    # Şimdilik örnek veri:
    # Gerçek uygulamada bu veriyi veritabanınızdan (stocks tablosu) veya harici API'den çekmelisiniz.
    # db = get_db()
    # stock_info = db.execute('SELECT * FROM stocks WHERE symbol = ?', (hisse_kodu,)).fetchone()
    # if stock_info:
    #     return jsonify(dict(stock_info))
    # else:
    #     return jsonify({"error": "Hisse bulunamadı"}), 404

    # Örnek veri setimizi genişletelim veya spesifik veriler sunalım:
    all_stock_details = {
        "GARAN": {"symbol": "GARAN", "name": "Garanti BBVA", "price": 320.50, "change": 2.45, "volume": "22.78M", "marketCap": "441.650B TL", "rsi": 57.8, "pivot": 318.50,"tahminDusukFiyat": 315.00, "tahminYuksekFiyat": 325.50, "description": "Garanti BBVA, Türkiye'nin önde gelen özel bankalarından biridir."},
        "ASELS": {"symbol": "ASELS", "name": "Aselsan Elektronik Sanayi", "price": 284.00, "change": 1.89, "volume": "18.45M", "marketCap": "932.145B TL", "rsi": 53.2, "pivot": 280.75, "description": "Aselsan, Türk Silahlı Kuvvetlerini Güçlendirme Vakfı tarafından yönetilen bir savunma sanayii şirketidir."},
        "THYAO": {"symbol": "THYAO", "name": "Türk Hava Yolları A.O.", "price": 135.75, "change": 3.12, "volume": "30.15M", "marketCap": "600.558B TL", "rsi": 59.1, "pivot": 132.40, "description": "Türk Hava Yolları, Türkiye'nin ulusal bayrak taşıyıcı havayolu şirketidir."}
        # Diğer hisselerin detayları...
    }
    
    stock_data = all_stock_details.get(hisse_kodu.upper()) # Gelen kodu büyük harfe çevirerek ara
    
    if stock_data:
        return jsonify(stock_data)
    else:
        # Eğer stocks tablonuz varsa ve oradan çekiyorsanız:
        # db = get_db()
        # stock_info_db = db.execute("SELECT symbol, name, price, change, volume, market_cap, rsi, pivot FROM stocks WHERE symbol = ?", (hisse_kodu.upper(),)).fetchone()
        # if stock_info_db:
        #     return jsonify(dict(stock_info_db))
        return jsonify({'error': f'{hisse_kodu} için detay bulunamadı'}), 404


# Eski /api/stocks route'unu /api/stocks_for_screener olarak değiştirdik.
# Eğer /api/stocks genel bir hisse listesi için kullanılıyorsa ve farklı bir amaç taşıyorsa onu koruyabilirsiniz.
# Şimdilik screener için olan API'yi daha belirgin isimlendirdik.

# Static dosyalar için route (genellikle Flask bunu otomatik yönetir static_folder belirtilince, bu özel route gerekmeyebilir)
# @app.route('/static/<path:filename>')
# def static_files(filename):
#     return send_from_directory('static', filename)

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static/css'): # static klasörü ve alt klasörleri otomatik oluşturulur Flask tarafından eğer static_folder belirtilmişse.
        os.makedirs('static/css')      # Bu kontroller gereksiz olabilir.
    if not os.path.exists('static/js'):
        os.makedirs('static/js')
    
    with app.app_context(): # init_db çağrısını app context'i içinde yapmak daha doğru
        init_db()
        
    app.run(debug=True)