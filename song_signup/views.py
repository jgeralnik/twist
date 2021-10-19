import logging
from datetime import datetime, timezone

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.shortcuts import render, redirect

from .forms import SingerForm, SongRequestForm
from .models import SongRequest

logger = logging.getLogger(__name__)


def _name_to_username(first_name, last_name):
    return f'{first_name.lower()}_{last_name.lower()}'


def get_all_songs(singer):
    songs_as_main_singer = singer.songrequest_set.all()
    songs_as_additional_singer = singer.songs.all()
    return (songs_as_main_singer | songs_as_additional_singer).distinct()


def get_all_songs_performed(singer):
    return get_all_songs(singer).exclude(performance_time=None)


def get_num_songs_performed(singer):
    return get_all_songs_performed(singer).count()


def get_how_long_waiting(singer):
    ordered_songs_performed = get_all_songs_performed(singer).order_by('-performance_time')

    if ordered_songs_performed:
        time_waiting = datetime.now(timezone.utc) - ordered_songs_performed[0].performance_time
    else:
        time_waiting = datetime.now(timezone.utc) - singer.date_joined

    return time_waiting.total_seconds()


def get_singers_next_songs(singer):
    # I'm using reverse request time, since we will eventually pop from the end of the list to get the earliest song.
    return list(get_all_songs(singer).filter(performance_time=None).order_by('-request_time'))


def calculate_singer_priority(singer):
    priority = pow(4, 1 / (get_num_songs_performed(singer) + 1)) * get_how_long_waiting(singer)
    logger.debug(f"Priority of {singer} is {priority}. Num songs performed: {get_num_songs_performed(singer)}. "
                 f"How long waiting: {get_how_long_waiting(singer)}")
    return priority


def assign_song_priorities():
    logger.info(" =====  START PRIORITISING PROCESS ========")
    current_priority = 1
    singer_queryset = User.objects.filter(is_superuser=False)  # Superusers don't need to be given priority

    songs_of_singers_dict = dict()
    for singer in singer_queryset:
        singer.priority = calculate_singer_priority(singer)
        next_songs = get_singers_next_songs(singer)
        for song in next_songs:
            song.priority = 0
            song.save()
        songs_of_singers_dict[singer.username] = next_songs

    prioritized_singers = [singer.username for singer in sorted(singer_queryset, key=lambda singer: singer.priority,
                                                                reverse=True)]
    logger.info(f"DONE PRIORITISING SINGERS: Singers priority is {prioritized_singers}")

    while songs_of_singers_dict:
        logger.info("* Staring singer cycle")
        singers_that_got_a_song = []
        for singer_username in prioritized_singers:
            if singer_username not in songs_of_singers_dict:
                continue

            # If a singer already got a song in this cycle (because he's singing with someone else), skipping this cycle
            if singer_username in singers_that_got_a_song:
                logger.info(f"Skipping {singer_username} as they already have a song in this cycle")
                continue

            if not songs_of_singers_dict[singer_username]:
                logger.debug(f"{singer_username} doesn't have songs left. Removing from cycle")
                del songs_of_singers_dict[singer_username]
                continue

            # Pop songs until we get a song that hasn't been assigned yet
            while songs_of_singers_dict[singer_username]:
                song = songs_of_singers_dict[singer_username].pop()
                if not SongRequest.objects.get(pk=song.pk).priority:
                    song.priority = current_priority
                    logger.debug(f"Dealing with {singer_username}: Setting priority of {song} to {current_priority}")
                    current_priority += 1
                    song.save()
                    singers_that_got_a_song.extend([singer.username for singer in song.additional_singers.all()])
                    break
                else:
                    logger.debug(
                        f"The song for {singer_username} ({song}) was already chosen, moving to singer's next song")

    logger.info("========== END PRIORITISING PROCESS ======")


def get_pending_songs_and_other_singers(user):
    songs_dict = {}

    for song in get_all_songs(user).filter(performance_time=None):
        songs_dict[song] = song.all_singers.all().exclude(pk=user.pk)

    return songs_dict


def song_signup(request):
    current_user = request.user
    song_lineup = get_all_songs(current_user).filter(performance_time=None)

    if not current_user.is_authenticated:
        return redirect('singer_login')

    if request.method == 'POST':
        form = SongRequestForm(request.POST, request=request)

        if form.is_valid():
            song_name = form.cleaned_data['song_name']
            musical = form.cleaned_data['musical']
            additional_singers = form.cleaned_data['additional_singers']

            try:
                existing_song = SongRequest.objects.get(song_name=song_name, musical=musical)
                if current_user in existing_song.additional_singers.all():
                    song_lineup = get_all_songs(current_user).filter(performance_time=None)
                    messages.error(request,
                                   f"Apparently {existing_song.singer} has already signed you up for this song")
                    return render(request, 'song_signup/song_signup.html', {
                        'form': form, 'song_lineup': song_lineup,
                        'song_lineup_with_singers': get_pending_songs_and_other_singers(current_user)
                    })
            except SongRequest.DoesNotExist:
                pass

            song_request = SongRequest(song_name=song_name, musical=musical, singer=current_user)
            song_request.priority = 0

            try:
                song_request.save()
                song_request.additional_singers.set(additional_singers)
                song_request.save()
                assign_song_priorities()
                return render(request, 'song_signup/signed_up.html', {
                    'song_lineup_with_singers': get_pending_songs_and_other_singers(current_user),
                    'song_lineup': song_lineup
                })

            except IntegrityError:
                messages.error(request, "You already signed up with this song tonight.")
                return render(request, 'song_signup/song_signup.html', {
                    'form': form,
                    'song_lineup_with_singers': get_pending_songs_and_other_singers(current_user),
                    'song_lineup': song_lineup
                })

    else:
        form = SongRequestForm(request=request)

    return render(request, 'song_signup/song_signup.html', {
        'form': form,
        'song_lineup_with_singers': get_pending_songs_and_other_singers(current_user),
        'song_lineup': song_lineup
    })


def singer_login(request, is_switching):
    if request.user.is_authenticated and not request.user.is_anonymous and not is_switching:
        return redirect('song_signup')

    if request.method == 'POST':
        form = SingerForm(request.POST)

        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            already_logged_in = form.cleaned_data['i_already_logged_in_tonight']

            if already_logged_in:
                try:
                    singer = User.objects.get(first_name=first_name, last_name=last_name)
                except User.DoesNotExist:
                    messages.error(request, "The name that you logged in with previously does not match your current "
                                            "name.\nCould there be a typo somewhere?")
                    return render(request, 'song_signup/singer_login.html', {'form': form})
                else:
                    if singer.is_superuser:
                        logout(request)
                        return redirect('admin:index')
            else:
                try:
                    singer = User.objects.create_user(
                        _name_to_username(first_name, last_name),
                        first_name=first_name,
                        last_name=last_name,
                        is_staff=True
                    )
                except IntegrityError:
                    messages.error(request, "The name that you're trying to login with already exists.\n"
                                            "Did you already login with us tonight? If so, check the box below.")
                    return render(request, 'song_signup/singer_login.html', {'form': form})

            group = Group.objects.get(name='singers')
            group.user_set.add(singer)
            login(request, singer)
            return redirect('song_signup')

    else:
        form = SingerForm()

    return render(request, 'song_signup/singer_login.html', {'form': form})


def delete_song_request(request, song_pk):
    SongRequest.objects.filter(pk=song_pk).delete()

    return redirect('song_signup')
