import datetime
import json
import os
from difflib import SequenceMatcher

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

# Create your views here.
from myapp.models import Registration, Complaints, Audio, LockedApp, LockedDocument
from myapp.train import train_user_model


def adminhome_get(request):
    return render(request,'adminhome.html')

def login_get(request):
    return render(request,'glasslogin.html')

def viewuser_get(request):
    a=Registration.objects.all()
    return render(request,'viewuser.html',{'data':a})

def viewcom_get(request):
    a=Complaints.objects.all()
    return render(request,'viewcomplaint.html', {'data':a})

def sentrep_get(request,id):
    a=Complaints.objects.get(id=id)
    return render(request, 'replies.html', {'data':a})

def sentrep_post(request):
    id=request.POST['id']
    reply=request.POST['reply']
    a=Complaints.objects.get(id=id)
    a.reply=reply
    a.status='replied'
    a.save()
    return redirect('/myapp/viewcom_get/')


def login_post(request):
    username=request.POST['username']
    password=request.POST['password']
    if not username or not password:
        messages.warning(request,'Username and Password is requested!')
    check=authenticate(request, username=username, password=password)
    if check is not None:
        login(request,check)
        if check.groups.filter(name='admin').exists():
            return redirect('/myapp/adminhome_get/')
        else:
            return redirect('/myapp/clienthome_get/')
    else:
        return redirect('/myapp/login_get/')

def adminchgpass_get(request):
    return render(request, 'changepass.html')

def adminchgpass_post(request):
    old_password=request.POST['old_password']
    new_password=request.POST['new_password']
    confirm_password=request.POST['confirm_password']
    a=request.user

    if a.check_password(old_password):
        if new_password == confirm_password:
            a.set_password(new_password)
            a.save()
            logout(request)
            return redirect('/myapp/login_get/')
        else:
            messages.warning(request, 'Passwords do not match!')
            return redirect('/myapp/adminchgpass_get/')
    else:
        messages.warning(request, 'Incorrect Current Password!')
        return redirect('/myapp/adminchgpass_get/')

def logout_get(request):
    logout(request)
    return redirect('/myapp/login_get/')


# â”€â”€â”€ Client Views â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def client_register_get(request):
    return render(request, 'client_register.html')


def client_register_post(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '').strip()
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phno = request.POST.get('phno', '').strip()
    gender = request.POST.get('gender', '').strip()
    dob = request.POST.get('dob', '').strip()
    country = request.POST.get('country', '').strip()
    voice_phrase = request.POST.get('voice_phrase', '').strip()

    if User.objects.filter(username=username).exists():
        messages.warning(request, 'Username already exists! Please choose another.')
        return redirect('/myapp/client_register_get/')

    user = User.objects.create_user(username=username, password=password, email=email)
    reg = Registration.objects.create(
        name=name, email=email, phno=phno, gender=gender,
        dob=dob, photo='', country=country, USER=user
    )
    Audio.objects.create(
        audio=voice_phrase.lower(),
        REGISTRATION=reg
    )
    login(request, user)
    messages.success(request, 'Registration successful! Please upload a voice file to continue.')
    return redirect('/myapp/uploadvoice_get/')


def client_voice_login_get(request):
    return render(request, 'client_voice_login.html')


def client_voice_login_post(request):
    username = request.POST.get('username', '').strip()
    voice_phrase = request.POST.get('voice_phrase', '').strip().lower()

    if not username:
        messages.warning(request, 'Please enter your username.')
        return redirect('/myapp/client_voice_login_get/')
    if not voice_phrase:
        messages.warning(request, 'Please record your voice passphrase.')
        return redirect('/myapp/client_voice_login_get/')

    try:
        user = User.objects.get(username=username)
        reg = Registration.objects.get(USER=user)
    except User.DoesNotExist:
        messages.warning(request, 'User not found. Please check your username.')
        return redirect('/myapp/client_voice_login_get/')
    except Registration.DoesNotExist:
        messages.warning(request, 'Client profile not found.')
        return redirect('/myapp/client_voice_login_get/')

    # â”€â”€ Passphrase text verification â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    phrase_record = Audio.objects.filter(REGISTRATION=reg, audio__gt='').first()
    stored_phrase = phrase_record.audio.strip().lower() if phrase_record else ''

    if not stored_phrase:
        messages.warning(request, 'No passphrase registered for this account.')
        return redirect('/myapp/client_voice_login_get/')

    similarity = SequenceMatcher(None, stored_phrase, voice_phrase).ratio()
    if similarity < 0.70:
        messages.warning(
            request,
            f'Passphrase did not match (similarity: {int(similarity * 100)}%). '
            'Speak the exact phrase you used during registration.'
        )
        return redirect('/myapp/client_voice_login_get/')

    # â”€â”€ Passed â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    login(request, user)
    return redirect('/myapp/clienthome_get/')


def clienthome_get(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    reg = Registration.objects.get(USER=request.user)
    complaints = Complaints.objects.filter(REGISTRATION=reg)
    locked_apps = LockedApp.objects.filter(REGISTRATION=reg, is_locked=True).count()
    locked_docs = LockedDocument.objects.filter(REGISTRATION=reg, is_locked=True).count()
    context = {
        'reg': reg,
        'complaints_count': complaints.count(),
        'replied_count': complaints.filter(status='replied').count(),
        'pending_count': complaints.filter(status='Pending').count(),
        'locked_apps_count': locked_apps,
        'locked_docs_count': locked_docs,
    }
    return render(request, 'clienthome.html', context)


def client_complaint_get(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    return render(request, 'client_complaint.html')


def client_complaint_post(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    complaint = request.POST.get('complaint', '').strip()
    if not complaint:
        messages.warning(request, 'Please enter a complaint.')
        return redirect('/myapp/client_complaint_get/')
    reg = Registration.objects.get(USER=request.user)
    Complaints.objects.create(
        date=datetime.date.today(),
        complaint=complaint,
        reply='',
        status='Pending',
        REGISTRATION=reg
    )
    messages.success(request, 'Your complaint has been submitted!')
    return redirect('/myapp/client_view_complaints_get/')


def client_view_complaints_get(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    reg = Registration.objects.get(USER=request.user)
    complaints = Complaints.objects.filter(REGISTRATION=reg).order_by('-id')
    return render(request, 'client_view_complaints.html', {'complaints': complaints})

def uploadvoice_get(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    try:
        reg = Registration.objects.get(USER=request.user)
        uploads = Audio.objects.filter(REGISTRATION=reg).exclude(audio_file='').order_by('-id')
        upload_count = uploads.count()
    except Registration.DoesNotExist:
        uploads = []
        upload_count = 0
    user_dir = os.path.join(settings.MEDIA_ROOT, 'voice_uploads', f'user_{request.user.id}')
    model_trained = os.path.exists(os.path.join(user_dir, 'model.pkl'))
    return render(request, 'voiceupload.html', {
        'uploads': uploads,
        'upload_count': upload_count,
        'model_trained': model_trained,
        'min_files': 3,
    })


def uploadvoice_post(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    if request.method != 'POST':
        return redirect('/myapp/uploadvoice_get/')

    voice_files = request.FILES.getlist('voice_files')
    if not voice_files:
        messages.warning(request, 'No files selected. Please choose at least one audio file.')
        return redirect('/myapp/uploadvoice_get/')

    try:
        reg = Registration.objects.get(USER=request.user)
    except Registration.DoesNotExist:
        messages.warning(request, 'Profile not found.')
        return redirect('/myapp/uploadvoice_get/')

    # Ensure user-specific directory exists under media/voice_uploads/user_<id>/
    user_dir = os.path.join(settings.MEDIA_ROOT, 'voice_uploads', f'user_{request.user.id}')
    os.makedirs(user_dir, exist_ok=True)

    uploaded_count = 0
    for voice_file in voice_files:
        safe_name = voice_file.name.replace(' ', '_')
        file_path = os.path.join(user_dir, safe_name)
        # Write file to disk manually so it lands in the user-specific directory
        with open(file_path, 'wb+') as dest:
            for chunk in voice_file.chunks():
                dest.write(chunk)
        relative_path = f'voice_uploads/user_{request.user.id}/{safe_name}'
        Audio.objects.create(
            date=datetime.date.today(),
            audio='',
            audio_file=relative_path,
            filename=safe_name,
            filesize=voice_file.size,
            REGISTRATION=reg
        )
        uploaded_count += 1

    if uploaded_count == 1:
        messages.success(request, f'"{voice_files[0].name}" uploaded successfully!')
    else:
        messages.success(request, f'{uploaded_count} files uploaded successfully!')

    # Auto-train (or re-train) when the user has enough samples
    total_uploads = Audio.objects.filter(REGISTRATION=reg).exclude(audio_file='').count()
    if total_uploads >= 3:
        try:
            train_user_model(request.user.id, user_dir)
            messages.success(
                request,
                f'Voice model trained with {total_uploads} sample(s). '
                'Please verify your voice to log in.'
            )
            logout(request)
            return redirect('/myapp/client_voice_login_get/')
        except Exception as e:
            messages.warning(request, f'Upload successful, but model training failed: {e}')
    else:
        remaining = 3 - total_uploads
        messages.warning(
            request,
            f'Upload at least {remaining} more file(s) to enable voice login '
            f'(currently {total_uploads}/3).'
        )

    return redirect('/myapp/uploadvoice_get/')


def uploadvoice_delete(request, audio_id):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    try:
        reg = Registration.objects.get(USER=request.user)
        audio = Audio.objects.get(id=audio_id, REGISTRATION=reg)
        # Remove the physical file from disk
        if audio.audio_file:
            file_on_disk = os.path.join(settings.MEDIA_ROOT, str(audio.audio_file))
            if os.path.exists(file_on_disk):
                os.remove(file_on_disk)
        audio.delete()
        messages.success(request, 'File deleted.')
        # Retrain model with remaining samples, or invalidate if below threshold
        user_dir = os.path.join(settings.MEDIA_ROOT, 'voice_uploads', f'user_{request.user.id}')
        remaining = Audio.objects.filter(REGISTRATION=reg).exclude(audio_file='').count()
        if remaining >= 3:
            try:
                train_user_model(request.user.id, user_dir)
            except Exception:
                pass  # best-effort retrain
        else:
            # Invalidate saved model so login is blocked until enough files are re-uploaded
            model_path = os.path.join(user_dir, 'model.pkl')
            if os.path.exists(model_path):
                os.remove(model_path)
            if remaining > 0:
                messages.warning(
                    request,
                    f'Voice model invalidated. Upload {3 - remaining} more file(s) to re-enable login.'
                )
    except (Registration.DoesNotExist, Audio.DoesNotExist):
        messages.warning(request, 'File not found.')
    return redirect('/myapp/uploadvoice_get/')


# â”€â”€â”€ Predefined app catalogue â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

DEFAULT_APPS = [
    {'key': 'whatsapp',   'name': 'WhatsApp',   'icon': 'ðŸ’¬'},
    {'key': 'instagram',  'name': 'Instagram',  'icon': 'ðŸ“¸'},
    {'key': 'facebook',   'name': 'Facebook',   'icon': 'ðŸ‘¤'},
    {'key': 'youtube',    'name': 'YouTube',    'icon': 'â–¶ï¸'},
    {'key': 'camera',     'name': 'Camera',     'icon': 'ðŸ“·'},
    {'key': 'gallery',    'name': 'Gallery',    'icon': 'ðŸ–¼ï¸'},
    {'key': 'messages',   'name': 'Messages',   'icon': 'âœ‰ï¸'},
    {'key': 'email',      'name': 'Email',      'icon': 'ðŸ“§'},
    {'key': 'contacts',   'name': 'Contacts',   'icon': 'ðŸ‘¥'},
    {'key': 'settings',   'name': 'Settings',   'icon': 'âš™ï¸'},
    {'key': 'browser',    'name': 'Browser',    'icon': 'ðŸŒ'},
    {'key': 'maps',       'name': 'Maps',       'icon': 'ðŸ—ºï¸'},
    {'key': 'calculator', 'name': 'Calculator', 'icon': 'ðŸ§®'},
    {'key': 'clock',      'name': 'Clock',      'icon': 'â°'},
    {'key': 'tiktok',     'name': 'TikTok',     'icon': 'ðŸŽµ'},
    {'key': 'snapchat',   'name': 'Snapchat',   'icon': 'ðŸ‘»'},
    {'key': 'twitter',    'name': 'Twitter/X',  'icon': 'ðŸ¦'},
    {'key': 'spotify',    'name': 'Spotify',    'icon': 'ðŸŽ¶'},
    {'key': 'netflix',    'name': 'Netflix',    'icon': 'ðŸŽ¬'},
    {'key': 'files',      'name': 'Files',      'icon': 'ðŸ“'},
]


def _get_stored_phrase(reg):
    """Return the stored voice passphrase for a registration, or empty string."""
    record = Audio.objects.filter(REGISTRATION=reg, audio__gt='').first()
    return record.audio.strip().lower() if record else ''


def _verify_phrase(stored, spoken):
    """Return (passed: bool, similarity_pct: int)."""
    if not stored:
        return False, 0
    ratio = SequenceMatcher(None, stored, spoken.strip().lower()).ratio()
    return ratio >= 0.70, int(ratio * 100)


# â”€â”€â”€ App Lock â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def applock_get(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    reg = Registration.objects.get(USER=request.user)
    # Seed the user's app list on first visit
    for app in DEFAULT_APPS:
        LockedApp.objects.get_or_create(
            app_key=app['key'], REGISTRATION=reg,
            defaults={'app_name': app['name'], 'icon': app['icon'], 'is_locked': False}
        )
    apps = LockedApp.objects.filter(REGISTRATION=reg)
    locked_count = apps.filter(is_locked=True).count()
    return render(request, 'applock.html', {
        'apps': apps,
        'reg': reg,
        'locked_count': locked_count,
    })


def applock_toggle_post(request, app_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    if request.user.is_staff or request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Admin cannot use app lock'})
    try:
        reg = Registration.objects.get(USER=request.user)
        app = LockedApp.objects.get(id=app_id, REGISTRATION=reg)
    except (Registration.DoesNotExist, LockedApp.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'App not found'})

    action = request.POST.get('action')  # 'lock' or 'unlock'

    if action == 'lock':
        app.is_locked = True
        app.save()
        return JsonResponse({'success': True, 'is_locked': True})

    elif action == 'unlock':
        voice_phrase = request.POST.get('voice_phrase', '').strip()
        if not voice_phrase:
            return JsonResponse({'success': False, 'error': 'Voice phrase required to unlock'})
        stored = _get_stored_phrase(reg)
        if not stored:
            return JsonResponse({'success': False, 'error': 'No passphrase registered for this account'})
        passed, pct = _verify_phrase(stored, voice_phrase)
        if passed:
            app.is_locked = False
            app.save()
            return JsonResponse({'success': True, 'is_locked': False})
        else:
            return JsonResponse({'success': False, 'error': f'Passphrase did not match ({pct}%). Speak clearly.'})

    return JsonResponse({'success': False, 'error': 'Invalid action'})


# â”€â”€â”€ Document Lock â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def doclock_get(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    reg = Registration.objects.get(USER=request.user)
    docs = LockedDocument.objects.filter(REGISTRATION=reg).order_by('-id')
    locked_count = docs.filter(is_locked=True).count()
    return render(request, 'doclock.html', {
        'docs': docs,
        'reg': reg,
        'locked_count': locked_count,
    })


def doclock_upload_post(request):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    if request.method != 'POST':
        return redirect('/myapp/doclock_get/')
    doc_file = request.FILES.get('doc_file')
    if not doc_file:
        messages.warning(request, 'No file selected.')
        return redirect('/myapp/doclock_get/')
    reg = Registration.objects.get(USER=request.user)
    ext = os.path.splitext(doc_file.name)[1].lower()
    LockedDocument.objects.create(
        name=doc_file.name,
        file=doc_file,
        file_type=ext,
        filesize=doc_file.size,
        is_locked=True,
        REGISTRATION=reg
    )
    messages.success(request, f'"{doc_file.name}" uploaded and locked.')
    return redirect('/myapp/doclock_get/')


def doclock_delete_post(request, doc_id):
    if not request.user.is_authenticated:
        return redirect('/myapp/client_voice_login_get/')
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/myapp/adminhome_get/')
    try:
        reg = Registration.objects.get(USER=request.user)
        doc = LockedDocument.objects.get(id=doc_id, REGISTRATION=reg)
        if doc.file:
            file_path = os.path.join(settings.MEDIA_ROOT, str(doc.file))
            if os.path.exists(file_path):
                os.remove(file_path)
        doc.delete()
        messages.success(request, 'Document deleted.')
    except (Registration.DoesNotExist, LockedDocument.DoesNotExist):
        messages.warning(request, 'Document not found.')
    return redirect('/myapp/doclock_get/')


def doclock_toggle_post(request, doc_id):
    """Toggle lock on a doc. Locking is free; unlocking requires voice phrase."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    if request.user.is_staff or request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Admin cannot use doc lock'})
    try:
        reg = Registration.objects.get(USER=request.user)
        doc = LockedDocument.objects.get(id=doc_id, REGISTRATION=reg)
    except (Registration.DoesNotExist, LockedDocument.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Document not found'})

    action = request.POST.get('action')  # 'lock' or 'unlock'

    if action == 'lock':
        doc.is_locked = True
        doc.save()
        return JsonResponse({'success': True, 'is_locked': True})

    elif action == 'unlock':
        voice_phrase = request.POST.get('voice_phrase', '').strip()
        if not voice_phrase:
            return JsonResponse({'success': False, 'error': 'Voice phrase required to unlock'})
        stored = _get_stored_phrase(reg)
        if not stored:
            return JsonResponse({'success': False, 'error': 'No passphrase registered'})
        passed, pct = _verify_phrase(stored, voice_phrase)
        if passed:
            doc.is_locked = False
            doc.save()
            return JsonResponse({'success': True, 'is_locked': False, 'download_url': doc.file.url, 'filename': doc.name})
        else:
            return JsonResponse({'success': False, 'error': f'Passphrase did not match ({pct}%). Speak clearly.'})

    return JsonResponse({'success': False, 'error': 'Invalid action'})


def doclock_access_post(request, doc_id):
    """Verify voice phrase and return a one-time download URL for a locked document."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    try:
        reg = Registration.objects.get(USER=request.user)
        doc = LockedDocument.objects.get(id=doc_id, REGISTRATION=reg)
    except (Registration.DoesNotExist, LockedDocument.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Document not found'})

    if not doc.is_locked:
        return JsonResponse({'success': True, 'download_url': doc.file.url, 'filename': doc.name})

    voice_phrase = request.POST.get('voice_phrase', '').strip()
    if not voice_phrase:
        return JsonResponse({'success': False, 'error': 'Voice phrase required'})

    stored = _get_stored_phrase(reg)
    if not stored:
        return JsonResponse({'success': False, 'error': 'No passphrase registered for this account'})

    passed, pct = _verify_phrase(stored, voice_phrase)
    if passed:
        return JsonResponse({'success': True, 'download_url': doc.file.url, 'filename': doc.name})
    else:
        return JsonResponse({'success': False, 'error': f'Passphrase did not match ({pct}%). Speak your exact registration phrase.'})


def doclock_rename_post(request, doc_id):
    """Rename a document's display name."""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'})
    try:
        reg = Registration.objects.get(USER=request.user)
        doc = LockedDocument.objects.get(id=doc_id, REGISTRATION=reg)
    except (Registration.DoesNotExist, LockedDocument.DoesNotExist):
        return JsonResponse({'success': False, 'error': 'Document not found'})
    new_name = request.POST.get('new_name', '').strip()
    if not new_name:
        return JsonResponse({'success': False, 'error': 'Name cannot be empty'})
    doc.name = new_name
    doc.save()
    return JsonResponse({'success': True, 'new_name': new_name})
