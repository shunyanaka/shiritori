import openai  # OpenAI GPT-3を使用するためのライブラリ

# OpenAI GPT-3のAPIキーを設定
openai.api_key = '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'

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 吹き出しのリストを初期化
shiritori_list = []
num = 0
text = ""
pre_text = ""

@app.route('/')


@app.route('/', methods=['GET', 'POST'])
def start():
    global shiritori_list  # グローバル変数を参照
    global num
    shiritori_list = []
    num = 0
    if request.method == 'POST':
        return redirect(url_for('shiritori'))
    return render_template('start.html')

@app.route('/shititori', methods=['GET', 'POST'])
def shiritori():
    global shiritori_list
    global num
    global text
    global pre_text

    if request.method == 'POST':

        # if num % 2 == 1:

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

        # user()

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
            # iie = "いいえ"
            # shiritori_list.append(iie)

        # if num % 2 == 0:   

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

def user():
    # render_template('shiritori.html', shiritori_list=shiritori_list)
    render_template('response.html', shiritori_list=shiritori_list)

@app.route('/result')
def result(text):
    render_template('result.html', text = text)

if __name__ == '__main__':
    app.run(debug=True)
