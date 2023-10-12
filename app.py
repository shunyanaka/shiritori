import openai  # OpenAI GPT-3を使用するためのライブラリ

# OpenAI GPT-3のAPIキーを設定
openai.api_key = ''

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 吹き出しのリストを初期化
shiritori_list = []
num = 0
text = ""

@app.route('/')


@app.route('/', methods=['GET', 'POST'])
def shiritori():
    global num
    global text
    num += 1

    if request.method == 'POST':

        # if num % 2 == 1:

        # フォームからテキストを取得
        text = request.form['text']

        # テキストを吹き出しリストに追加
        shiritori_list.append(text)

        # user()

        japanese = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            # {"role": "system", "content": "ChatGPTへの指示"},
            {"role": "user", "content": f"「{text}」という日本語は存在しますか。「はい」か「いいえ」のみで答えてください。"}
            ]   
        )
        if (japanese['choices'][0]['message']['content'] == "いいえ"):
            iie = "いいえ"
            shiritori_list.append(iie)
            render_template('result.html', text = text)
            # return redirect(url_for('result', text = text))

        # if num % 2 == 0:   

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
            # {"role": "system", "content": "ChatGPTへの指示"},
            {"role": "user", "content": f"「{text[-1]}」から始まる単語を1つだけ述べてください。ただし、「{text[-1]}」が小文字なら大文字に変換してください。「ん」で終わる言葉は避けてください。"}
            ]   
        )
        shiritori_list.append(response['choices'][0]['message']['content'])

    return render_template('shiritori.html', shiritori_list=shiritori_list)

def user():
    # render_template('shiritori.html', shiritori_list=shiritori_list)
    render_template('response.html', shiritori_list=shiritori_list)

@app.route('/result')
def result(text):
    render_template('result.html', text = text)


if __name__ == '__main__':
    app.run(debug=True)
