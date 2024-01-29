from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('login', views.login, name='login'),
    path('home', views.home, name='home'),
    path('home/<str:new_song>', views.home, name='home'),
    path('home/<str:new_song>', views.home, name='home'),
    path('spotlight_data', views.spotlight_data, name='spotlight_data'),
    path('dashboard_data', views.dashboard_data, name='dashboard_data'),
    path('faq', views.faq, name='faq'),
    path('tip_us', views.tip_us, name='tip_us'),
    path('logout', views.logout, name='logout'),
    path('manage_songs', views.manage_songs, name='manage_songs'),
    path('view_suggestions', views.view_suggestions, name='view_suggestions'),
    path('add_song', views.add_song, name='add_song'),
    path('rename_song', views.rename_song, name='rename_song'),
    path('suggest_song', views.suggest_song, name='suggest_song'),
    path('add_song_request', views.add_song_request, name='add_song_request'),
    path('get_current_songs', views.get_current_songs, name='get_current_songs'),
    path('get_current_user', views.get_current_user, name='get_current_user'),
    path('get_suggested_songs', views.get_suggested_songs, name='get_suggested_songs'),
    path('delete_song/<int:song_pk>', views.delete_song, name='delete_song'),
    path('get_song/<int:song_pk>', views.get_song, name='get_song'),
    path('lyrics/<int:song_pk>', views.lyrics, name='lyrics'),
    path('group_lyrics/<int:song_pk>', views.group_lyrics, name='group_lyrics'),
    path('alternative_lyrics/<int:song_pk>', views.alternative_lyrics, name='alternative_lyrics'),
    path('alternative_group_lyrics/<int:song_pk>', views.alternative_group_lyrics, name='alternative_group_lyrics'),
    path('lyrics_by_id/<int:lyrics_id>', views.lyrics_by_id, name='lyrics_by_id'),
    path('default_lyrics', views.default_lyrics, name='default_lyrics'),
    path('reset_database', views.reset_database, name='reset_database'),
    path('enable_signup', views.enable_signup, name='enable_signup'),
    path('disable_signup', views.disable_signup, name='disable_signup'),
    path('signup_disabled', views.signup_disabled, name='signup_disabled'),
    path('recalculate_priorities', views.recalculate_priorities, name='recalculate_priorities'),
    path('upload_lineapp_orders', views.upload_lineapp_orders, name='upload_lineapp_orders')
]

