from flask import Flask, render_template, request, redirect, session, url_for
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SESSION_COOKIE_SECURE'] = True   
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Mapeamento visual melhorado das cartas com emojis coloridos
carta_visual = {
    'A♠': '🂡', '2♠': '🂢', '3♠': '🂣', '4♠': '🂤', '5♠': '🂥', '6♠': '🂦', '7♠': '🂧', '8♠': '🂨', '9♠': '🂩', '10♠': '🂪', 'J♠': '🂫', 'Q♠': '🂭', 'K♠': '🂮',
    'A♥': '🂱', '2♥': '🂲', '3♥': '🂳', '4♥': '🂴', '5♥': '🂵', '6♥': '🂶', '7♥': '🂷', '8♥': '🂸', '9♥': '🂹', '10♥': '🂺', 'J♥': '🂻', 'Q♥': '🂽', 'K♥': '🂾',
    'A♦': '🃁', '2♦': '🃂', '3♦': '🃃', '4♦': '🃄', '5♦': '🃅', '6♦': '🃆', '7♦': '🃇', '8♦': '🃈', '9♦': '🃉', '10♦': '🃊', 'J♦': '🃋', 'Q♦': '🃍', 'K♦': '🃎',
    'A♣': '🃑', '2♣': '🃒', '3♣': '🃓', '4♣': '🃔', '5♣': '🃕', '6♣': '🃖', '7♣': '🃗', '8♣': '🃘', '9♣': '🃙', '10♣': '🃚', 'J♣': '🃛', 'Q♣': '🃝', 'K♣': '🃞'
}

# Baralho completo com naipes
baralho_completo = [f'{valor}{naipe}' for naipe in ['♠', '♥', '♦', '♣'] for valor in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']]

conquistas = {
    'vitoria_rapida': {'nome': 'Vitória Relâmpago', 'desc': 'Vença em menos de 10 segundos', 'desbloqueada': False},
    'rei_ases': {'nome': 'Rei dos Ases', 'desc': 'Tenha 3 Ases em uma mão', 'desbloqueada': False}
}

def calcular_pontuacao(mao):
    total = 0
    ases = 0
    
    for carta in mao:
        if carta == '??':
            continue
        
        # Extrai apenas o valor da carta (remove o naipe)
        valor = carta[:-1] if len(carta) > 1 and carta[-1] in '♠♥♦♣' else carta
        
        if valor in ['J', 'Q', 'K']:
            total += 10
        elif valor == 'A':
            ases += 1
            total += 11
        else:
            total += int(valor)
    
    while total > 21 and ases:
        total -= 10
        ases -= 1
    
    return total

def registrar_historico(resultado, aposta):
    historico = session.get('historico', [])
    historico.insert(0, {
        'data': datetime.now().strftime('%H:%M:%S'),
        'resultado': resultado,
        'aposta': aposta
    })
    session['historico'] = historico[:5]

@app.route('/')
def index():
    session['saldo'] = session.get('saldo', 200)
    session.setdefault('historico', [])
    return render_template('index.html', 
                         saldo=session['saldo'],
                         historico=session['historico'])

@app.route('/apostar', methods=['POST'])
def apostar():
    try:
        aposta = int(request.form['aposta'])
    except ValueError:
        return redirect(url_for('index'))
    
    if aposta <= 0 or aposta > session.get('saldo', 200):
        return redirect(url_for('index'))

    session['aposta'] = aposta
    session['baralho'] = random.sample(baralho_completo, len(baralho_completo))
    session['jogador'] = [session['baralho'].pop(), session['baralho'].pop()]
    session['dealer'] = [session['baralho'].pop(), '??']
    session['game_over'] = False
    
    # Verificar blackjack natural
    if calcular_pontuacao(session['jogador']) == 21:
        session['game_over'] = True
        return redirect(url_for('resultado'))
    
    session['inicio_partida'] = datetime.now().timestamp()
    
    session['pode_double'] = True
    
    return redirect(url_for('game'))

@app.route('/instrucoes')
def instrucoes():
    return render_template('instructions.html')

@app.route('/game')
def game():
    if session.get('game_over', False):
        return redirect(url_for('resultado'))
    
    pontuacao = calcular_pontuacao(session['jogador'])
    pontuacao_dealer = calcular_pontuacao([session['dealer'][0]]) if session['dealer'][1] == '??' else calcular_pontuacao(session['dealer'])
    
    if pontuacao > 21:
        session['game_over'] = True
        return redirect(url_for('resultado'))
    
    ases = sum(1 for carta in session['jogador'] if carta.startswith('A'))
    if ases >= 3 and not conquistas['rei_ases']['desbloqueada']:
        conquistas['rei_ases']['desbloqueada'] = True
        session['conquista'] = conquistas['rei_ases']
    
    return render_template('game.html', 
                         jogador=session['jogador'], 
                         dealer=session['dealer'],
                         pontuacao=pontuacao,
                         pontuacao_dealer=pontuacao_dealer,
                         cartas=carta_visual,
                         pode_double=session.get('pode_double', False),
                         saldo=session.get('saldo', 200),
                         aposta=session.get('aposta', 0))

@app.route('/acao', methods=['POST'])
def acao():
    if session.get('game_over', False):
        return redirect(url_for('resultado'))
    
    acao = request.form['acao']
    session.modified = True
    
    if acao == 'Hit':
        nova_carta = session['baralho'].pop()
        session['jogador'].append(nova_carta)
        
        if calcular_pontuacao(session['jogador']) > 21:
            session['game_over'] = True
            return redirect(url_for('resultado'))
            
        # Adiciona o parâmetro updated=1 no redirecionamento
        return redirect(url_for('game', updated=1))  # <--- AQUI
    
    elif acao == 'Stand':
        session['dealer'][1] = session['baralho'].pop()
        
        while calcular_pontuacao(session['dealer']) < 17:
            session['dealer'].append(session['baralho'].pop())
        
        session['game_over'] = True
    
    elif acao == 'Double':
        if session.get('pode_double', False) and len(session['jogador']) == 2:
            session['aposta'] *= 2
            session['pode_double'] = False
            
            nova_carta = session['baralho'].pop()
            session['jogador'].append(nova_carta)
            
            # Forçar Stand após Double
            session['dealer'][1] = session['baralho'].pop()
            while calcular_pontuacao(session['dealer']) < 17:
                session['dealer'].append(session['baralho'].pop())
            
            session['game_over'] = True
            return redirect(url_for('resultado'))
    
    return redirect(url_for('game'))

@app.route('/resultado')
def resultado():
    if not session.get('game_over', False):
        return redirect(url_for('game'))
    
    pont_jogador = calcular_pontuacao(session['jogador'])
    pont_dealer = calcular_pontuacao(session['dealer'])
    
    # Verificar blackjack natural (21 com apenas 2 cartas)
    blackjack_jogador = pont_jogador == 21 and len(session['jogador']) == 2
    blackjack_dealer = pont_dealer == 21 and len(session['dealer']) == 2
    
    if pont_jogador > 21:
        resultado = 'Você estourou! 😭'
        session['saldo'] -= session['aposta']
    elif pont_dealer > 21:
        resultado = 'Dealer estourou! Você venceu! 🎉'
        session['saldo'] += session['aposta']
    elif blackjack_jogador and not blackjack_dealer:
        resultado = 'Blackjack! Você venceu! 🎉🎉'
        session['saldo'] += int(session['aposta'] * 1.5)  # Pagamento especial para blackjack
    elif blackjack_dealer and not blackjack_jogador:
        resultado = 'Dealer fez Blackjack! Você perdeu! 💀'
        session['saldo'] -= session['aposta']
    elif blackjack_jogador and blackjack_dealer:
        resultado = 'Empate com Blackjack! 🤝'
    elif pont_jogador > pont_dealer:
        resultado = 'Você venceu! 🎉'
        session['saldo'] += session['aposta']
    elif pont_jogador == pont_dealer:
        resultado = 'Empate! 🤝'
    else:
        resultado = 'Dealer venceu! 💀'
        session['saldo'] -= session['aposta']

    registrar_historico(resultado, session['aposta'])
    
    tempo_partida = datetime.now().timestamp() - session.get('inicio_partida', 0)
    if tempo_partida < 10 and not conquistas['vitoria_rapida']['desbloqueada']:
        conquistas['vitoria_rapida']['desbloqueada'] = True
        session['conquista'] = conquistas['vitoria_rapida']
    
    return render_template('result.html',
                         jogador=session['jogador'],
                         dealer=session['dealer'],
                         pont_jogador=pont_jogador,
                         pont_dealer=pont_dealer,
                         resultado=resultado,
                         historico=session['historico'],
                         conquista=session.pop('conquista', None),
                         saldo=session['saldo'],
                         cartas=carta_visual)

@app.after_request
def after_request(response):
    if session.modified:
        session.permanent = True
    return response

@app.route('/historico')
def historico():
    return render_template('historical.html', historico=session.get('historico', []))

@app.route('/conquistas')
def conquistas_view():
    return render_template('achivements.html', conquistas=conquistas)

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)