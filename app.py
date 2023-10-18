import openai  # OpenAI GPT-3を使用するためのライブラリ

# OpenAI GPT-3のAPIキーを設定
openai.api_key = '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'

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# データベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shiritori.db'
db = SQLAlchemy(app)

# モデルの作成
class Player(db.Model):
    __tablename__="player"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    count = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

# 吹き出しのリストを初期化
shiritori_list = []
num = 0
text = ""
pre_text = ""

@app.route('/', methods=['GET', 'POST'])
def start():
    global shiritori_list  # グローバル変数を参照
    global num
    shiritori_list = []
    num = 0
    if request.method == 'POST':
        return redirect(url_for('shiritori'))
    players = Player.query.order_by(Player.count.desc()).all()
    return render_template('start.html', players=players)

@app.route('/shititori', methods=['GET', 'POST'])
def shiritori():
    global shiritori_list
    global num
    global text
    global pre_text

    if request.method == 'POST':

        # フォームからテキストを取得
        text = request.form['text']

        if text[-1] == 'ん':
            message = "「ん」で終わる言葉を使いました！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        if num != 0 and text[0] != pre_text[-1]:
            message = f"「{pre_text[-1]}」という文字から始めていません！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        if text in shiritori_list:
            message = f"「{text}」という言葉を使うのは二度目です！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # テキストを吹き出しリストに追加
        shiritori_list.append(text)

        japanese = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            # {"role": "system", "content": "「はい」か「いいえ」のみで答えてください。"},
            {"role": "user", "content": f"「{text}」という言葉は存在しますか。「はい」か「いいえ」のみで答えてください。"}
            ]   
        )
        if (japanese['choices'][0]['message']['content'] == "いいえ"):
            message = f"「{text}」という言葉は存在しません！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            # {"role": "system", "content": "あなたはしりとりをしています。与えられた言葉の最後の文字から始まる言葉を1つだけ述べてください。例えば「東京」が与えられたら、最後の文字である「う」から始まる言葉を述べてください。「」"},
            {"role": "system", "content": "回答は全て平仮名にしてください。「ん」で終わる回答はしないでください。"},
            {"role": "user", "content": f"「{text[-1]}」から始まる単語を1つだけ述べてください。ただし、「ん」で終わる回答はやめてください。「{text[-1]}」が小文字なら大文字に変換してください。漢字やカタカナではなく平仮名で答えてください。"}
            # {"role": "user", "content": f"「{text}」の最後の文字から始まる言葉を1つだけ述べてください。例えば、「東京」ならば、「う」から始まる言葉です。ただし、最後の文字が小文字なら大文字に変換してください。また、「ん」で終わる言葉は避けてください。"}
            ]   
        )
        shiritori_list.append(response['choices'][0]['message']['content'])

        pre_text = response['choices'][0]['message']['content']

        num+=1

    return render_template('shiritori.html', shiritori_list=shiritori_list,num=num)

@app.route('/save_score', methods=['POST'])
def save_score():
    player_name = request.form['player_name']
    count = int(request.form['count'])

    player = Player(name=player_name, count=count)
    db.session.add(player)
    db.session.commit()

    return redirect(url_for('start'))

if __name__ == '__main__':
    app.run(debug=True)

