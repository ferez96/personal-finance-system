import json
import os

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from docx import Document as DocxDocument
from docx.enum.style import WD_STYLE_TYPE

from .forms import DocumentForm
from .models import Document
from .utils import (
    format_document,
    set_normal_style,
    set_heading_styles,
    get_paragraphs_and_headings
)


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


@require_POST
def delete_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    # Delete the file from the filesystem
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
    if os.path.isfile(file_path):
        os.remove(file_path)

    # Delete the Document object from the database
    doc.delete()

    messages.success(request, 'Document deleted successfully.')
    return redirect(reverse('editor:list_documents'))


def edit_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
    document = DocxDocument(file_path)

    # Use utility function to get paragraphs and headings
    paragraphs, headings = get_paragraphs_and_headings(document)

    context = {
        'document': doc,
        'paragraphs': paragraphs,
        'headings': headings
    }
    return render(request, 'editor/edit_document.html', context)


@csrf_protect
def update_heading(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            doc_id = data.get('doc_id')
            para_index = int(data.get('para_index'))
            style_name = data.get('style_name')

            doc = get_object_or_404(Document, id=doc_id)
            file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
            document = DocxDocument(file_path)

            # Try to access the style directly
            try:
                style = document.styles[style_name]
            except KeyError:
                # Style doesn't exist, create it if it's a heading style
                if style_name.startswith('Heading '):
                    new_style = document.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)
                    new_style.base_style = document.styles['Normal']

                    style = new_style
                    print(f"Created new style: {style} for Document: {doc}")
                elif style_name == 'Normal':
                    style = document.styles['Normal']
                else:
                    return JsonResponse(
                        {'status': 'error', 'message': f'Style "{style_name}" not found and cannot be created.'}
                    )

            # Update the style of the specified paragraph
            para = document.paragraphs[para_index]
            para.style = style

            # Save the document
            document.save(file_path)

            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(e)  # Log the error
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


def apply_format(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
    document = DocxDocument(file_path)

    # Apply formatting functions
    document = format_document(document)
    document = set_normal_style(document)
    document = set_heading_styles(document)

    # Save the formatted document
    document.save(file_path)

    return redirect(reverse('editor:edit_document', args=[doc_id]))


def download_document(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
    with open(file_path, 'rb') as f:
        response = HttpResponse(
            f.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename=Modified_{os.path.basename(file_path)}'
        return response