import json
from flask import Flask, render_template, request, redirect, url_for, session
import openai

app = Flask(__name__)
app.secret_key = "super secret key"
para1 = '''I hope this letter finds you well. I am writing to you today
 to discuss a matter of importance regarding a financial
 transaction that took place between us. Specifically, I
am requesting that you pay back the sum of $500 to me.'''

para2 = '''As you may recall, I loaned you this money on [date] with
 the understanding that it would be paid back in a timely
 manner. However, it has been [insert time frame] since
 that loan and I have yet to receive any repayment from
 you. I have reached out to you multiple times to inquire
 about the status of the repayment, but have yet to
 receive a response.'''

para3 = '''I understand that financial difficulties can arise, but I
 kindly ask that you make every effort to repay the
 loan as soon as possible. I have faith that you will do
 the right thing and pay back the money that I loaned
 you. Please let me know your plan of action and
 when I can expect to receive the money.\n\nYour sincerely,\n[Name]'''

with open(r'/Users/amiaynarayan/Projects/credential.json') as config_file:
    config = json.load(config_file)

openai.api_key = config.get("OPENAI_API_KEY")

def generate_letter(subject, word_count=200):
    '''Method to return the first draft of letters'''
    search_query = f'I want to write a letter about "{subject}". I want the letter to be {word_count} words long.  Please use around 75 words per paragraph. \
        please write the letter.'
    completions = openai.Completion.create(
        engine="text-davinci-003",
        prompt=search_query,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    print(completions)
    letter = completions.choices[0].text
    print(letter)
    return letter

def paragraph_letter(letter):
    '''Break a letter into paragraphs'''
    letter = letter.strip('\n')
    letter_array = letter.split('\n\n')
    paragraphed_letter = letter_array[1:len(letter_array)-1]
    return paragraphed_letter

@app.route('/button', methods=['GET'])
def button():
    return render_template('button.html')

@app.route('/', methods=['GET', 'POST'])
def parameters():
    if request.method == 'POST':
        # Remove the below line
        paras = f'\n\nDear [name],\n\n{para1}\n\n{para2}\n\n{para3}'
        letter_type = request.form['instruction']
        word_count = request.form['word_count']
        letter_generated = paras or generate_letter(letter_type, word_count)
        paragraphed_letter = paragraph_letter(letter_generated)
        return render_template('edit.html', paragraphed_letter=paragraphed_letter)
    return render_template('parameters.html')

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    if request.method == 'POST':
        paragraphs = request.form.getlist('paragraph')
        return render_template('finalise.html', paragraphs=paragraphs)

@app.route('/edit_para', methods=['GET', 'POST'])
def edit_para():
    paragraphs = request.form
    print('the form is ', paragraphs)
    return render_template('edit.html', paragraphed_letter=session.get('paragraphs'))

@app.route('/finalise', methods=['GET', 'POST'])
def finalise():
    if request.method == 'POST':
        letter = request.form['letter']
        return render_template('letter.html', letter=letter)
    return render_template('finalise.html')

@app.route('/letter')
def letter():
    return render_template('letter.html')

if __name__ == '__main__':
    app.run(debug=True)
