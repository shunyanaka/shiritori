import openai  # OpenAI GPT-3を使用するためのライブラリ
import re, os

# OpenAI GPT-3のAPIキーを環境変数から設定
openai.api_key = os.environ.get('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("APIキーが設定されていません。環境変数OPENAI_API_KEYを確認してください。")

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

# 小文字を大文字に変換する関数
def convert_to_large_char(char):
    small_to_large = {
        "ぁ": "あ",
        "ぃ": "い",
        "ぅ": "う",
        "ぇ": "え",
        "ぉ": "お",
        "っ": "つ",
        "ゃ": "や",
        "ゅ": "ゆ",
        "ょ": "よ",
        "ゎ": "わ",
    }
    return small_to_large.get(char, char) # 値のキーと存在しない場合のデフォルト値

# 末尾の文字（ーを無視）を取得する
def get_last_character(string):
    # 文字列が「ー」だけで構成されている場合、Noneを返す
    #if re.fullmatch(r"ー+", string):
    #    return None

    match = re.search(r"([^ー])ー*$", string)
    if match:
        return match.group(1)
    return None

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

        tail = get_last_character(text)
        if tail == None:
            message = f"まもるくんは「{text}」という言葉を知らないよ！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # if text[-1] == 'ん':
        if tail == 'ん':
            message = "「ん」で終わる言葉を使ったよ！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # 前の「しり」の文字が小文字なら、大文字に変換
        if num != 0:
            char = convert_to_large_char(pre_text[-1])

        # if num != 0 and text[0] != pre_text[-1]:
        if num != 0 and text[0] != char:
            # message = f"「{pre_text[-1]}」という文字から始めてないよ！"
            message = f"「{char}」という文字から始めてないよ！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        if text in shiritori_list:
            message = f"「{text}」という言葉を使うのは二度目だよ！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # テキストを吹き出しリストに追加
        shiritori_list.append(text)

        japanese = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            # {"role": "system", "content": "「はい」か「いいえ」のみで答えてください。"},
            {"role": "user", "content": f"「{text}」という言葉は存在しますか。「はい」か「いいえ」のみで答えてください。ただし、漢字やカタカナが平仮名で入力されている可能性を考慮してください。"}
            ]   
        )
        if (japanese['choices'][0]['message']['content'] == "いいえ"):
            message = f"まもるくんは「{text}」という言葉を知らないよ！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # 「しり」の文字が小文字なら、大文字に変換
        shiri = convert_to_large_char(text[-1])

        max_attempts = 3
        attempts = 0
        while attempts < max_attempts:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                # {"role": "system", "content": "あなたはしりとりをしています。与えられた言葉の最後の文字から始まる言葉を1つだけ述べてください。例えば「東京」が与えられたら、最後の文字である「う」から始まる言葉を述べてください。「」"},
                {"role": "system", "content": "回答は全て平仮名にしてください。「ん」で終わる回答はしないでください。1つの単語のみを平仮名で回答してください。"},
                # {"role": "user", "content": f"「{text[-1]}」から始まる単語を1つだけ述べてください。ただし、「ん」で終わる回答はやめてください。「{text[-1]}」が小文字なら大文字に変換してください。漢字やカタカナではなく平仮名で答えてください。"}
                {"role": "user", "content": f"「{shiri}」から始まる単語を1つだけ述べてください。ただし、「ん」で終わる回答はやめてください。「{shiri}漢字やカタカナではなく平仮名で答えてください。"}
                # {"role": "user", "content": f"「{text}」の最後の文字から始まる言葉を1つだけ述べてください。例えば、「東京」ならば、「う」から始まる言葉です。ただし、最後の文字が小文字なら大文字に変換してください。また、「ん」で終わる言葉は避けてください。"}
                ]   
            )
            res = response['choices'][0]['message']['content']
            if res[-1] != 'ん' and res not in shiritori_list:
                break
            attempts += 1

        if attempts == 3:
            message = f"まもるくんは次の言葉が思い浮かばないよ！"
            return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        shiritori_list.append(res)
        # shiritori_list.append(response['choices'][0]['message']['content'])
        pre_text = res
        # pre_text = response['choices'][0]['message']['content']

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
