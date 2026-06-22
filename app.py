from flask import Flask, render_template, request, redirect, url_for, session
import random
import os

app = Flask(__name__)
app.secret_key = "bomba_acar"

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
    return render_template('index.html', mode_selection=True, total_available=len(BUTUN_SUALAR))

@app.route('/start/<mode>')
def start_quiz(mode):
    session.clear()
    indeksler = list(range(len(BUTUN_SUALAR)))
    
    if mode == 'random':
        limit = request.args.get('limit', default=25, type=int)
        range_end = request.args.get('range_end', default=len(BUTUN_SUALAR), type=int)
        range_end = max(1, min(len(BUTUN_SUALAR), range_end))
        hovuz = indeksler[:range_end]
        secilmis_indeksler = random.sample(hovuz, min(len(hovuz), limit))
    else:
        start_from = request.args.get('start', default=1, type=int)
        start_idx = max(0, start_from - 1)
        secilmis_indeksler = indeksler[start_idx:]

    if not secilmis_indeksler:
        return redirect(url_for('index'))

    session['sual_idleri'] = secilmis_indeksler
    session['current_index'] = 0
    session['cavablar'] = [""] * len(secilmis_indeksler)
    return redirect(url_for('quiz'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'sual_idleri' not in session: return redirect(url_for('index'))

    curr_idx = session['current_index']
    sual_idleri = session['sual_idleri']

    if request.method == 'POST':
        action = request.form.get('action', 'submit')
        
        # Əvvəlki suala qayıt
        if action == 'prev' and curr_idx > 0:
            session['current_index'] = curr_idx - 1
            session.modified = True
            return redirect(url_for('quiz'))
        
        # Cavab təsdiq et
        if action == 'submit':
            istifadeci_cavabi = request.form.get('cavab', '').strip().lower()
            if istifadeci_cavabi:
                cavablar = list(session.get('cavablar', []))
                if len(cavablar) < len(sual_idleri):
                    cavablar.extend([""] * (len(sual_idleri) - len(cavablar)))
                cavablar[curr_idx] = istifadeci_cavabi
                session['cavablar'] = cavablar
                session['current_index'] = curr_idx + 1
                session.modified = True
                
                if session['current_index'] >= len(sual_idleri):
                    return redirect(url_for('result'))
                return redirect(url_for('quiz'))

    if curr_idx < len(sual_idleri):
        sual_id = sual_idleri[curr_idx]
        cari_cavablar = session.get('cavablar', [])
        if len(cari_cavablar) < len(sual_idleri):
            cari_cavablar.extend([""] * (len(sual_idleri) - len(cari_cavablar)))
        
        duz_sayi = 0
        sehv_sayi = 0
        sidebar_status = []
        
        for i in range(len(sual_idleri)):
            ans = cari_cavablar[i]
            if not ans:
                status = "unanswered"
            else:
                s_id = sual_idleri[i]
                s_no = BUTUN_SUALAR[s_id][0].split('.')[0].strip()
                if ans == DUZGUN_CAVABLAR.get(s_no, ""):
                    duz_sayi += 1
                    status = "correct"
                else:
                    sehv_sayi += 1
                    status = "incorrect"
            sidebar_status.append({'index': i, 'number': i+1, 'status': status})
        
        return render_template('index.html', 
                               sual=BUTUN_SUALAR[sual_id], 
                               no=curr_idx+1, 
                               total=len(sual_idleri),
                               duz_sayi=duz_sayi,
                               sehv_sayi=sehv_sayi,
                               can_go_back=(curr_idx > 0),
                               sidebar_status=sidebar_status,
                               curr_idx=curr_idx)
    return redirect(url_for('result'))

@app.route('/jump/<int:index>')
def jump(index):
    if 'sual_idleri' not in session: return redirect(url_for('index'))
    sual_idleri = session['sual_idleri']
    if 0 <= index < len(sual_idleri):
        session['current_index'] = index
        session.modified = True
    return redirect(url_for('quiz'))

@app.route('/result')
def result():
    cavablar_raw = session.get('cavablar', [])
    sual_idleri = session.get('sual_idleri', [])
    
    cavablar = []
    for i, ans in enumerate(cavablar_raw):
        if not ans:
            ans = "boş"
        s_id = sual_idleri[i]
        s_no = BUTUN_SUALAR[s_id][0].split('.')[0].strip()
        duz_c = DUZGUN_CAVABLAR.get(s_no, "")
        cavablar.append({
            'no': s_no,
            'user': ans,
            'correct': duz_c,
            'status': (ans == duz_c)
        })
        
    is_finished = session.get('current_index', 0) >= len(sual_idleri)
    return render_template('index.html', result=True, cavablar=cavablar, is_finished=is_finished)

@app.route('/basic-result')
def basic_result():
    cavablar_raw = session.get('cavablar', [])
    sual_idleri = session.get('sual_idleri', [])
    
    cavablar = []
    for i, ans in enumerate(cavablar_raw):
        if not ans:
            ans = "boş"
        s_id = sual_idleri[i]
        s_no = BUTUN_SUALAR[s_id][0].split('.')[0].strip()
        duz_c = DUZGUN_CAVABLAR.get(s_no, "")
        cavablar.append({
            'no': s_no,
            'user': ans,
            'correct': duz_c,
            'status': (ans == duz_c)
        })
        
    is_finished = session.get('current_index', 0) >= len(sual_idleri)
    return render_template('index.html', 
                         basic_result=True,  # ✅ Yeni parametr
                         cavablar=cavablar, 
                         is_finished=is_finished)

if __name__ == "__main__":
    app.run(debug=True)