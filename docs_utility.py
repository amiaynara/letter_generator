from googleapiclient.errors import HttpError

def get_doc_argument(parsed_response, type='resume'):
    '''Method to generate proper values for placeholders in the template google document'''
    google_doc_content = {
        'main_head' : parsed_response.get('main_head') or 'main heading',
        'short_description' : parsed_response.get('short_description') or '<suitable subheading>',
        'head' : parsed_response.get('head') or ['topic 1', 'topic 2', 'topic 3'],
        'content' : parsed_response.get('content') or ['1'* 100, '2'* 200, '3' * 300],
    }
    return google_doc_content

def get_placeholder(key, index=None):
    '''Get placeholder for a particular key'''
    place_holder = '{{' + (f'{key}{index}' if index else key) + '}}'
    return place_holder

def create_document(service, drive_service, parsed_response):
    # create a new, empty document
    # body = {
    #     'title': 'importance of doctors'
    # }
    # doc = service.documents().create(body=body).execute()
    # get content required to populate the document
    try:
        google_doc_content = get_doc_argument(parsed_response)
        # create a new document based on the template
        template_id = '1zHdZWXJoTIw3_Flssomv0Lz_732Eq25O_lUMWDVy27k' #id for pet resume
        # drive service to copy a file
        copy_title = google_doc_content.get('main_head') or 'hot doc created using ai'
        body = {'name': copy_title,}
        drive_response = drive_service.files().copy(fileId=template_id, body=body).execute()
        document_copy_id = drive_response.get('id')


        #doc = service.documents().copy(body=body).execute()
        # Get the content of the template document

        # Replace the placeholders in the document
        requests = []
        for key, value in google_doc_content.items():
            if isinstance(value, list):
                for index, item in enumerate(value):
                    requests.append({
                        'replaceAllText': {
                            'containsText': {
                                'text': get_placeholder(key, index + 1),
                                'matchCase': 'true'
                            },
                            'replaceText': item
                        }
                    }) 
            if isinstance(value, str):
                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': get_placeholder(key),
                            'matchCase': 'true'
                        },
                        'replaceText': value
                    }
                })
        service.documents().batchUpdate(documentId=document_copy_id, body={'requests': requests}).execute()

        # Print the document ID and URL
        print('Created document with title: {0}'.format(body.get('name')))
        return 'https://drive.google.com/open?id={0}'.format(document_copy_id)
    except Exception as error:
        return f'ERROR: Something wrong occurred. \n{error}'

def get_document(service, document_id):
    try:
        # Retrieve the documents contents from the Docs service.
        return service.documents().get(documentId=document_id).execute()
    except HttpError as err:
        print(err)
        return 'error'