import os
import openai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow

# --- Setup your keys ---
openai.api_key = "OPENAI_API_KEY"
openai.api_base = "NOTION_API_KEY"

# --- Define Google Drive access scope ---
SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/documents.readonly']

# --- Authenticate with Google ---
def authenticate_google():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

# --- Get Google Docs text ---
def extract_text_from_doc(doc_id, creds):
    service = build('docs', 'v1', credentials=creds)
    doc = service.documents().get(documentId=doc_id).execute()
    text = ''
    for element in doc.get("body").get("content"):
        paragraph = element.get("paragraph")
        if paragraph:
            for run in paragraph.get("elements"):
                if "textRun" in run:
                    text += run["textRun"]["content"]
    return text

# --- Generate a summary using OpenRouter ---
def summarize(text):
    prompt = f"""
You are an AI portfolio assistant. Read the user's project content and summarize it as a portfolio item with the following structure:

Title:
Skills Used:
Problem:
Solution:
Result:
Short Summary:

Here is the raw content:
{text}
    """
    response = openai.ChatCompletion.create(
        model="meta-llama/llama-3-8b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
    )
    return response["choices"][0]["message"]["content"]

# --- Main run ---
def main():
    creds = authenticate_google()
    drive_service = build('drive', 'v3', credentials=creds)

    # List Google Docs
    results = drive_service.files().list(
        q="mimeType='application/vnd.google-apps.document'",
        pageSize=5,
        fields="files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print("No documents found.")
    else:
        for item in items:
            print(f"📄 Found: {item['name']}")
            text = extract_text_from_doc(item['id'], creds)
            summary = summarize(text)
            print("✅ AI Summary:\n", summary)
            print("-" * 50)

if __name__ == "__main__":
    main()
