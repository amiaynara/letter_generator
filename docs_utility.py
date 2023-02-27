from googleapiclient.errors import HttpError


def create_document(service):
    # Create a new, empty document
    body = {
        'title': 'My New Document from google docs api'

    }
    doc = service.documents().create(body=body).execute()
    body = {
        'title': 'Importance of Doctors'
    }
    doc = service.documents().create(body=body).execute()

    # Add a heading to the document
    requests = [
        {
            'insertText': {
                'location': {
                    'index': 1
                },
                'text': 'Doctor\n'
            }
        },
        {
            'createHeader': {}
        },
        {
            'insertText': {
                'location': {
                    'index': 0
                },
                'text': 'Doctors are a very important part of society. They must be protected.\n'
            }
        }
    ]
    service.documents().batchUpdate(documentId=doc['documentId'], body={'requests': requests}).execute()


    # Print the document ID and URL
    print('Created document with title: {0}'.format(doc.get('title')))
    print('Document URL: https://drive.google.com/open?id={0}'.format(doc.get('documentId')))

def get_document(service, document_id):
    try:
        # Retrieve the documents contents from the Docs service.
        return service.documents().get(documentId=document_id).execute()
    except HttpError as err:
        print(err)
        return 'error'