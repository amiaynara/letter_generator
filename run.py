import base64
import json
import os
import re
from flask import Flask, render_template, request, session, url_for, jsonify, redirect
import openai

from docs_utility import create_document, get_document

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
    search_query = f'Given is a paragraph:\n{paragraph}\n. Include the original text of the paragraph but add {instruction}'
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
    search_query = f'Given is a letter:\n{letter}\n. Include the original text of the letter, but add {instruction}. Also structure the letter into paragraphs.'
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

##### Google docs API routes #####
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build

def generate_brochure(instruction):
    search_query = f'{instruction}'

    extra_info = 'Write a good heading. Write 3 paragraphs, 30 words each. Begin each paragraph with a 1 word title, without colon'
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f'{search_query}. {extra_info}',
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )
    response_text = response.choices[0].text
    return response_text

def parse_response(response):
    parsed_response = {'main_head': '', 'head': [], 'content': []}
    parsed_response['main_head'] = response.strip().split('\n\n')[0].rstrip()
    for para in response.strip().split('\n\n')[1:]:
        head, paragraph = para.split(':')
        parsed_response['head'].append(head)
        parsed_response['content'].append(paragraph)
    return parsed_response


@app.route('/generate_doc', methods=['GET', 'POST'])
def generate_doc():
    if request.method == 'POST':
        # Remove the below line
        sample_doc = {'main_head': 'iPhone 14 Pro: The Ultimate Smartphone', 'head': ['Revolution', 'Performance', 'Features'], 'content': [' The iPhone 14 Pro marks a major step forward in smartphone technology. With its cutting-edge A14 Bionic processor, 5G support, and advanced camera system, the Pro is a device that will appeal to power users and casual users alike. Its sleek design and powerful specs make it the perfect choice for anyone looking for a top-of-the-line device.', ' The A14 Bionic processor is the fastest chip ever in a smartphone, offering incredible speed and performance. Coupled with 5G support, the Pro is capable of downloading and streaming content faster than ever before. Its advanced camera system offers professional-grade photos and videos, and its long-lasting battery ensures that you can stay connected all day long.', ' The Pro also boasts an array of features, including a stunning OLED display, Face ID, and an all-new gesture control system. With its powerful processor, 5G support, and advanced camera system, the Pro is the perfect device for anyone looking for the ultimate in smartphone technology.']}
        instruction = request.form['instruction']
        image_file = request.files['image_file'] or None
        session['image'] = bool(image_file)
        prod_root = '/home/coolexpert/letter_generator'
        local_root = '/Users/amiaynarayan/Projects/innovateIQ/letter_generator/'
        if bool(image_file):
            session['image'] = {'filename': image_file.filename} 
            image_file.save(os.path.join(prod_root, f'static/images/{image_file.filename}'))
        chatGPT_response = generate_brochure(instruction)
        parsed_response = parse_response(chatGPT_response) # may be this method could be docs_utilty.py
        session['document'] = parsed_response
        return render_template('doc.html', document=parsed_response)
    return render_template('parameters.html')

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
LOCAL_CLIENT_SECRETS_FILE = "client_secret.json"
CLIENT_SECRETS_FILE = "/home/coolexpert/keys/client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive',
    ]
API_SERVICE_NAME = 'docs'
API_VERSION = 'v1'
DOCUMENT_ID = '18HKKU-xOVcSE-7r7kjigXXzYwiQd25hJN4pSvUbijzI'

@app.route('/test', methods=['GET'])
def test_api_request():
    if 'credentials' not in session:
        return redirect('authorize')
    
    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **session['credentials'])

    docs_service = build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    parsed_response = session.get('document', None)
    if not parsed_response:
        return redirect(url_for('parameters'))
    has_image = session.get('image')
    response = create_document(docs_service, drive_service, parsed_response, has_image)
    if response.get('error'):
        return render_template('400_bad_request.html', message=response.get('error')) 

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    session['credentials'] = credentials_to_dict(credentials)
    # may be the below can be replaced with a page, if need be
    link = response.get('doc_link')
    return f'<a href="{link}">Link to the created doc</a>'


@app.route('/oauth2callback')
def oauth2callback():
  # Specify the state when creating the flow in the callback so that it can
  # verified in the authorization server response.
  state = session['state']

  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
  flow.redirect_uri = url_for('oauth2callback', _external=True)

  # Use the authorization server's response to fetch the OAuth 2.0 tokens.
  authorization_response = request.url
  flow.fetch_token(authorization_response=authorization_response)

  # Store credentials in the session.
  # ACTION ITEM: In a production app, you likely want to save these
  #              credentials in a persistent database instead.
  credentials = flow.credentials
  session['credentials'] = credentials_to_dict(credentials)

  return redirect(url_for('test_api_request'))


@app.route('/authorize')
def authorize():
  # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
  flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      CLIENT_SECRETS_FILE, scopes=SCOPES)

  # The URI created here must exactly match one of the authorized redirect URIs
  # for the OAuth 2.0 client, which you configured in the API Console. If this
  # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
  # error.
  flow.redirect_uri = url_for('oauth2callback', _external=True)
  print('the created url is', flow.redirect_uri)

  authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

  # Store the state so the callback can verify the auth server response.
  session['state'] = state

  return redirect(authorization_url)

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

@app.route('/clear')
def clear_credentials():
    if 'credentials' in session:
        del session['credentials']
    return ('Credentials have been cleared.<br><br>' + '<h1>Amiay</h1>')


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    app.run(debug=True)
