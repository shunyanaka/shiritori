# ライブラリインストール
import openai
import re, os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

# OpenAI GPT-3のAPIキーを環境変数から設定
openai.api_key = os.environ.get('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("APIキーが設定されていません。環境変数OPENAI_API_KEYを確認してください。")

app = Flask(__name__)

# セッションの秘密鍵
app.secret_key = os.urandom(24)

# データベースの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shiritori.db'
db = SQLAlchemy(app)

# データベースのモデルの作成
class Player(db.Model):
    __tablename__="player"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    count = db.Column(db.Integer, nullable=False)

# データベース作成
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
    return small_to_large.get(char, char) # 値のキー：存在しない場合のデフォルト値

# 「ー」の文字を無視して末尾の文字を取得する
def get_last_character(string):
    #match = re.search(r"([^ー])ー*$", string)
    #match = re.search(r"([^ー])ー*$", string)
    match = re.search(r"([^ー」])ー*」*$", string)
    if match:
        return match.group(1)
    return None

# しりとりのセッションをリセットするヘルパー関数
def reset_shiritori_session():
    session['shiritori_list'] = []
    session['num'] = 0
    session['text'] = ""
    session['pre_text'] = ""

# 履歴、しりとり回数、自分の回答、相手の回答
# shiritori_list = []
#num = 0
#text = ""
#pre_text = ""

# スタート画面の処理
@app.route('/', methods=['GET', 'POST'])
def start():
    reset_shiritori_session()
    #global shiritori_list  # グローバル変数を参照
    #global num
    #shiritori_list = [] # 履歴を初期化
    #num = 0
    if request.method == 'POST':
        return redirect(url_for('shiritori'))
    players = Player.query.order_by(Player.count.desc()).all()
    return render_template('start.html', players=players)

# しりとりをする処理
@app.route('/shititori', methods=['GET', 'POST'])
def shiritori():
    if 'shiritori_list' not in session:
        reset_shiritori_session()
    #global shiritori_list
    #global num
    #global text
    #global pre_text

    if request.method == 'POST':

        # フォームからテキストを取得
        text = request.form['text']

        # 「ー」を除いて最後の文字を取得
        tail = get_last_character(text)

        # 「ー」のみの言葉を入力した場合にしりとり終了
        if tail == None:
            message = f"まもるくんは「{text}」という言葉を知らないよ！"
            #return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)
            return render_template('result.html', num=session['num'], message=message,shiritori_list=session['shiritori_list'])

        # 「ん」で終わったときにしりとり終了
        if tail == 'ん':
            message = "「ん」で終わる言葉を使ったよ！"
            return render_template('result.html', num=session['num'], message=message,shiritori_list=session['shiritori_list'])
            #return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        #char1 = get_last_character(session['pre_text'])

        # 相手の「しり」の文字が小文字なら、大文字に変換（２回目以降）
        #if num != 0:
        if session['num'] != 0:
            #char = convert_to_large_char(pre_text[-1])
            #char2 = convert_to_large_char(char1)
            char2 = convert_to_large_char(session['pre_text'])

        # 言葉の「しり」を取っていなければしりとり終了
        #if num != 0 and text[0] != char:
        if session['num'] != 0 and text[0] != char2:
            message = f"「{char2}」という文字から始めてないよ！"
            return render_template('result.html', num=session['num'], message=message,shiritori_list=session['shiritori_list'])
            #return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # 同じ言葉を２回使用するとしりとり終了
        # if text in shiritori_list:
        #if text in shiritori_list:
        if text in session['shiritori_list']:
            message = f"「{text}」という言葉を使うのは二度目だよ！"
            return render_template('result.html', num=session['num'], message=message,shiritori_list=session['shiritori_list'])
            #return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # 回答を履歴に追加
        #shiritori_list.append(text)
        session['shiritori_list'].append(text)

        # ユーザの回答が言葉として存在するかを判定
        japanese = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            # {"role": "system", "content": ""},
            {"role": "user", "content": f"「{text}」という言葉は存在しますか。「はい」か「いいえ」のみで答えてください。ただし、漢字やカタカナが平仮名で入力されている可能性を考慮してください。"}
            ]   
        )

        # ユーザの回答が言葉として存在しない場合、しりとり終了
        if (japanese['choices'][0]['message']['content'] == "いいえ"):
            message = f"まもるくんは「{text}」という言葉を知らないよ！"
            return render_template('result.html', num=session['num'], message=message,shiritori_list=session['shiritori_list'])
            #return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # ユーザの回答の「しり」の文字が小文字なら、大文字に変換
        shiri = convert_to_large_char(text[-1])

        # AIの回答の「しり」の文字が「ん」、もしくは同じ言葉を２度回答したときに、最大３回再生成
        max_attempts = 3
        attempts = 0
        while attempts < max_attempts:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                {"role": "system", "content": "1つの単語のみを平仮名で回答してください。"},
                {"role": "user", "content": f"「{shiri}」から始まる単語を1つだけ述べてください。ただし、「ん」で終わる回答はやめてください。漢字やカタカナではなく平仮名で答えてください。"}
                ]   
            )
            res = response['choices'][0]['message']['content']

            session['pre_text'] = get_last_character(res)

            #if res[-1] != 'ん' and res not in shiritori_list:
            #if res[-1] != 'ん' and res not in session['shiritori_list']:
            if session['pre_text'] != 'ん' and res not in session['shiritori_list']:
                break
            attempts += 1

        # AIが３度NG回答をしたとき、しりとり終了
        if attempts == 3:
            message = f"まもるくんは次の言葉が思い浮かばないよ！"
            return render_template('result.html', num=session['num'], message=message,shiritori_list=session['shiritori_list'])
            # return render_template('result.html', num=num, message=message,shiritori_list=shiritori_list)

        # AIの回答を履歴に追加
        #shiritori_list.append(res)
        session['shiritori_list'].extend([res])

        # AIの解答を記録
        #pre_text = res
        #session['pre_text'] = res

        # しりとりの回数をインクリメント
        #num+=1
        session['num'] += 1

    return render_template('shiritori.html', shiritori_list=session['shiritori_list'], num=session['num'])
    #return render_template('shiritori.html', shiritori_list=shiritori_list,num=num)

# しりとりの回数を記録する処理
@app.route('/save_score', methods=['POST'])
def save_score():

    # ユーザの名前としりとりの回数を代入
    player_name = request.form['player_name']
    count = int(request.form['count'])

    # データベースに保存
    player = Player(name=player_name, count=count)
    db.session.add(player)
    db.session.commit()

    return redirect(url_for('start'))

if __name__ == '__main__':
    is_debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=is_debug)
    #app.run(debug=True)
