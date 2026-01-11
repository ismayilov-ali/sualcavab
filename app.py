from flask import Flask, render_template, request, redirect, url_for, session
import random
import os

app = Flask(__name__)
app.secret_key = "gizli_acar_buraya"

def duzsual():
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
        return sualar
    except FileNotFoundError:
        return []

@app.route('/')
def index():
    butun_sualar = duzsual()
    secilmis = random.sample(butun_sualar, min(len(butun_sualar), 5))
    
    session['sualar'] = secilmis
    session['current_index'] = 0
    session['cavablar'] = []
    
    return redirect(url_for('quiz'))

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'sualar' not in session:
        return redirect(url_for('index'))

    index = session['current_index']
    sualar = session['sualar']

    if request.method == 'POST':
        cavab = request.form.get('cavab')
        if cavab:
            session['cavablar'].append(cavab)
            session['current_index'] += 1
            session.modified = True
            
            if session['current_index'] >= len(sualar):
                return redirect(url_for('result'))
            return redirect(url_for('quiz'))

    if index < len(sualar):
        hazirki_sual = sualar[index]
        return render_template('index.html', sual=hazirki_sual, no=index+1, total=len(sualar))
    
    return redirect(url_for('result'))

@app.route('/result')
def result():
    cavablar = session.get('cavablar', [])
    return render_template('index.html', result=True, cavablar=cavablar)

if __name__ == "__main__":
    app.run(debug=True)