from django.shortcuts import render, redirect
from .forms import DocumentForm
from .models import Document
from django.urls import reverse
from docx import Document as DocxDocument
import os
from django.conf import settings
from django.http import JsonResponse, HttpResponse

def list_documents(request):
    documents = Document.objects.all()
    return render(request, 'editor/list_documents.html', {'documents': documents})

def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save()
            return redirect(reverse('editor:list_documents'))
    else:
        form = DocumentForm()
    return render(request, 'editor/upload.html', {'form': form})

def edit_document(request, doc_id):
    doc = Document.objects.get(id=doc_id)
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
    document = DocxDocument(file_path)

    # Extract paragraphs and their styles
    paragraphs = []
    for i, para in enumerate(document.paragraphs):
        text = para.text
        style = para.style.name
        paragraphs.append({'index': i, 'text': text, 'style': style})

    context = {
        'document': doc,
        'paragraphs': paragraphs
    }
    return render(request, 'editor/edit_document.html', context)

def update_heading(request):
    if request.method == 'POST':
        doc_id = request.POST.get('doc_id')
        para_index = int(request.POST.get('para_index'))
        heading_level = int(request.POST.get('heading_level'))

        doc = Document.objects.get(id=doc_id)
        file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
        document = DocxDocument(file_path)

        # Update the style of the specified paragraph
        para = document.paragraphs[para_index]
        para.style = f'Heading {heading_level}'

        # Save the document
        document.save(file_path)

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

def apply_format(request, doc_id):
    # Define your predefined formats here
    # For demonstration, let's set all paragraphs to 'Normal' style
    doc = Document.objects.get(id=doc_id)
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
    document = DocxDocument(file_path)

    for para in document.paragraphs:
        para.style = 'Normal'

    document.save(file_path)
    return redirect(reverse('editor:edit_document', args=[doc_id]))

def download_document(request, doc_id):
    doc = Document.objects.get(id=doc_id)
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename=Modified_{os.path.basename(file_path)}'
        return response
