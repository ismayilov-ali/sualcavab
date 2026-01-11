from flask import Flask, render_template, request, redirect, url_for, session
import random
import os

app = Flask(__name__)
app.secret_key = "test_key_12345" # Təhlükəsizlik üçün sessiya açarı

BUTUN_SUALAR = []

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

# Proqram başlayanda sualları yükləyirik
suallari_yukle()

@app.after_request
def add_header(response):
    # Brauzerin köhnə nəticə səhifəsini yaddaşda saxlamasına icazə vermirik
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def index():
    # Yenidən başla funksiyası üçün sessiyanı tam təmizləyirik
    session.clear()
    if not BUTUN_SUALAR:
        suallari_yukle()
    
    # Kuki limitini aşmamaq üçün yalnız ID-ləri saxlayırıq
    indeksler = list(range(len(BUTUN_SUALAR)))
    secilmis_indeksler = random.sample(indeksler, min(len(BUTUN_SUALAR), 25))
    
    session['sual_idleri'] = secilmis_indeksler
    session['current_index'] = 0
    session['cavablar'] = []
    return redirect(url_for('quiz'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'sual_idleri' not in session:
        return redirect(url_for('index'))

    curr_idx = session['current_index']
    sual_idleri = session['sual_idleri']

    if request.method == 'POST':
        cavab = request.form.get('cavab', '').strip()
        if cavab:
            sual_id = sual_idleri[curr_idx]
            original_sual = BUTUN_SUALAR[sual_id][0]
            sual_no = original_sual.split('.')[0]
            
            cavablar = list(session.get('cavablar', []))
            cavablar.append(f"{sual_no}. {cavab}")
            session['cavablar'] = cavablar
            session['current_index'] = curr_idx + 1
            session.modified = True
            
            if session['current_index'] >= len(sual_idleri):
                return redirect(url_for('result'))
            return redirect(url_for('quiz'))

    if curr_idx < len(sual_idleri):
        sual_id = sual_idleri[curr_idx]
        return render_template('index.html', sual=BUTUN_SUALAR[sual_id], no=curr_idx+1, total=len(sual_idleri))
    return redirect(url_for('result'))

@app.route('/result')
def result():
    cavablar = session.get('cavablar', [])
    return render_template('index.html', result=True, cavablar=cavablar)

if __name__ == "__main__":
    app.run(debug=True)