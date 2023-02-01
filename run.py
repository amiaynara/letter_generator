import json
import re
from flask import Flask, render_template, request, session
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

# choose appriate location of keys
amiay_dev = r'/Users/amiaynarayan/Projects/credential.json'
python_anywhere = r'/home/coolexpert/keys/ten_question_config.json'
with open(python_anywhere) as config_file:
    config = json.load(config_file)

# constants
DEFAULT_WORD_COUNT  = 150
openai.api_key = config.get("OPENAI_API_KEY")

def generate_letter(subject, word_count=DEFAULT_WORD_COUNT):
    '''Method to return the first draft of letters'''
    search_query = f'Write a 3 paragraph document about "{subject}". I want the letter to be {word_count} words long.\
        please write the letter.'
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=search_query,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    letter = response.choices[0].text
    return letter

def modify_para(paragraph, instruction):
    search_query = f'Keeping this instruction in mind: {instruction}; modify the paragraph:\n{paragraph}'
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=search_query,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    new_paragraph = response.choices[0].text
    return new_paragraph.replace('"', '').replace('\n', '')

def modify_letter(letter, instruction):
    search_query = f'Given is a letter. Keeping this instruction in mind: {instruction}; modify the letter:\n{letter}. Also structure the letter into paragraphs.'
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=search_query,
        max_tokens=2048,
        n=1,
        stop=None,
        temperature=0.5,
    )
    modified_letter = response.choices[0].text
    print(modified_letter)
    return modified_letter.replace('"', '')

def paragraph_letter(letter):
    '''Break a letter into paragraphs'''
    letter = letter.strip('\n')
    letter_array = letter.split('\n\n')
    paragraphed_letter = letter_array
    return paragraphed_letter

@app.route('/', methods=['GET', 'POST'])
def parameters():
    if request.method == 'POST':
        # Remove the below line
        paras = f'\n\nDear [name],\n\n{para1}\n\n{para2}\n\n{para3}'
        letter_type = request.form['instruction']
        # word_count = request.form['word_count']
        letter_generated = generate_letter(letter_type)
        # process the response of chatgpt to convert it into paragraphs
        paragraphed_letter = paragraph_letter(letter_generated)
        if len(paragraphed_letter) >= 2:
            session['paragraphed_letter'] = paragraphed_letter
        return render_template('edit.html', paragraphed_letter=paragraphed_letter)
    return render_template('parameters.html')


@app.route('/edit_para', methods=['GET', 'POST'])
def edit_para():
    if request.method == 'POST':
        data = request.form
        keys = data.keys()
        # find the paragraph index that is to be changed
        paragraph_index = None
        regx = r'instruction_(?P<digit>\d+)'
        paragraphs = {}
        for key in keys:
            if 'instruction' in key and data.get(key):
                match = re.search(regx, key)
                if match:
                    paragraph_index = match.group('digit')
            if 'para' in key:
                paragraphs[key] = data.get(key)
        instruction = data.get(f'instruction_{paragraph_index}')
        if paragraph_index and instruction:
            # if there is actually a valid change requested
            modified_para = modify_para(data.get(f'para_{paragraph_index}'), instruction)
            paragraphs[f'para_{paragraph_index}'] = modified_para
            session['paragraphed_letter'] = paragraphs
        else:
            # the request is missing the para_<id> then return the same letter.
            final_letter = '\n\n'.join(paragraphs.values())
            session['paragraphed_letter'] = paragraphs
            return render_template('finalise.html', letter=final_letter)
        return render_template('edit.html', paragraphed_letter=paragraphs.values())
    paragraphed_letter = session.get('paragraphed_letter') or []
    if paragraphed_letter:
        return render_template('edit.html', paragraphed_letter=paragraphed_letter.values())
    return render_template('400_bad_request.html')

@app.route('/finalise', methods=['GET', 'POST'])
def finalise():
    if request.method == 'POST':
        data = request.form
        letter = data.get('letter').replace('\n', '')
        instruction = data.get('instruction')
        modified_letter = modify_letter(letter, instruction)
        return render_template('finalise.html', letter=modified_letter, modified=True)
    return render_template('finalise.html')

if __name__ == '__main__':
    app.run(debug=True)
