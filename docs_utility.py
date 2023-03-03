from googleapiclient.errors import HttpError


def create_document(service, drive_service, content):
    # Create a new, empty document
    # body = {
    #     'title': 'Importance of Doctors'
    # }
    # doc = service.documents().create(body=body).execute()

    # Create a new document based on the template
    template_id = '1YyX0vGK1L0J-YhTfENtV5m1MVMEV9Z71ZUq95cRR1as'
    # drive service to copy a file
    copy_title = 'Hot Doc Created using AI'
    body = {
        'name': copy_title,
    }
    drive_response = drive_service.files().copy(
        fileId=template_id, body=body).execute()
    document_copy_id = drive_response.get('id')


    #doc = service.documents().copy(body=body).execute()
    # Get the content of the template document

    # Replace the placeholders in the document
    requests = []
    requests.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{para1}}',
                    'matchCase': 'true'
                },
                'replaceText': content[0]
            }
        },
    )
    requests.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{para2}}',
                    'matchCase': 'true'
                },
                'replaceText': content[1]
            }
        },
    )
    requests.append(
        {
            'replaceAllText': {
                'containsText': {
                    'text': '{{para3}}',
                    'matchCase': 'true'
                },
                'replaceText': content[2]
            }
        },
    )   
    service.documents().batchUpdate(documentId=document_copy_id, body={'requests': requests}).execute()

    # Print the document ID and URL
    print('Created document with title: {0}'.format(body.get('name')))
    print('Document URL: https://drive.google.com/open?id={0}'.format(document_copy_id))

def get_document(service, document_id):
    try:
        # Retrieve the documents contents from the Docs service.
        return service.documents().get(documentId=document_id).execute()
    except HttpError as err:
        print(err)
        return 'error'