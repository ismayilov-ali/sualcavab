from flask import Flask, render_template, request, redirect, url_for, session
import random
import os

app = Flask(__name__)
app.secret_key = "bomba_acar" # Təhlükəsizlik açarı

BUTUN_SUALAR = []
DUZGUN_CAVABLAR = {}

def suallari_yukle():
    global BUTUN_SUALAR
    sualar_path = os.path.join("txt", "sualar.txt")
    try:
        with open(sualar_path, "r", encoding="utf-8") as f:
            sualar = []
            alt_sualar = []
            n = 1
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if not line: continue
                if line.startswith(f"{n}."):
                    if alt_sualar: sualar.append(alt_sualar)
                    alt_sualar = [line]
                    n += 1
                else:
                    alt_sualar.append(line)
            if alt_sualar: sualar.append(alt_sualar)
        BUTUN_SUALAR = sualar
    except FileNotFoundError:
        BUTUN_SUALAR = []

def cavablari_yukle():
    global DUZGUN_CAVABLAR
    cavablar_path = os.path.join("cavablar", "cavablar.txt")
    try:
        with open(cavablar_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "." not in line: continue
                hisseler = line.split(".", 1)
                no = hisseler[0].strip()
                cavab = hisseler[1].strip().lower()
                DUZGUN_CAVABLAR[no] = cavab
    except FileNotFoundError:
        DUZGUN_CAVABLAR = {}

suallari_yukle()
cavablari_yukle()

@app.route('/')
def index():
    # Ümumi mövcud sual sayını interfeysə göndəririk
    return render_template('index.html', mode_selection=True, total_available=len(BUTUN_SUALAR))

@app.route('/start/<mode>')
def start_quiz(mode):
    session.clear()
    indeksler = list(range(len(BUTUN_SUALAR)))
    
    if mode == 'random':
        secilmis_indeksler = random.sample(indeksler, min(len(BUTUN_SUALAR), 25))
    else:
        # URL-dən 'start' parametrini götürürük, yoxdursa 1-dən başlayırıq
        start_from = request.args.get('start', default=1, type=int)
        start_idx = max(0, start_from - 1) # Python indeksi üçün 1 çıxılır
        secilmis_indeksler = indeksler[start_idx:]

    if not secilmis_indeksler:
        return redirect(url_for('index'))

    session['sual_idleri'] = secilmis_indeksler
    session['current_index'] = 0
    session['cavablar'] = []
    return redirect(url_for('quiz'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'sual_idleri' not in session: return redirect(url_for('index'))

    curr_idx = session['current_index']
    sual_idleri = session['sual_idleri']

    if request.method == 'POST':
        istifadeci_cavabi = request.form.get('cavab', '').strip().lower()
        if istifadeci_cavabi:
            sual_id = sual_idleri[curr_idx]
            sual_no = BUTUN_SUALAR[sual_id][0].split('.')[0].strip()
            duzgun_cavab = DUZGUN_CAVABLAR.get(sual_no, "")
            
            is_correct = (istifadeci_cavabi == duzgun_cavab)
            
            cavablar = list(session.get('cavablar', []))
            cavablar.append({
                'no': sual_no,
                'user': istifadeci_cavabi,
                'correct': duzgun_cavab,
                'status': is_correct
            })
            session['cavablar'] = cavablar
            session['current_index'] = curr_idx + 1
            session.modified = True
            
            if session['current_index'] >= len(sual_idleri):
                return redirect(url_for('result'))
            return redirect(url_for('quiz'))

    if curr_idx < len(sual_idleri):
        sual_id = sual_idleri[curr_idx]
        cari_cavablar = session.get('cavablar', [])
        duz_sayi = len([c for c in cari_cavablar if c['status'] == True])
        sehv_sayi = len([c for c in cari_cavablar if c['status'] == False])
        
        return render_template('index.html', 
                               sual=BUTUN_SUALAR[sual_id], 
                               no=curr_idx+1, 
                               total=len(sual_idleri),
                               duz_sayi=duz_sayi,
                               sehv_sayi=sehv_sayi)
    return redirect(url_for('result'))

@app.route('/result')
def result():
    cavablar = session.get('cavablar', [])
    is_finished = session.get('current_index', 0) >= len(session.get('sual_idleri', []))
    return render_template('index.html', result=True, cavablar=cavablar, is_finished=is_finished)

if __name__ == "__main__":
    app.run(debug=True)