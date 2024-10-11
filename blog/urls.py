from django.urls import path

from . import views
from .views import PostListView
from .feeds import LatestPostsFeed

app_name = 'blog'

urlpatterns = [
    # POST views
    path('',views.index, name='index'),
    path('blog/', PostListView.as_view(), name='post_list'),
    path('posts/tag/<slug:tag_slug>/', views.PostListView.as_view(), name='post_list_by_tag'),
    path('<int:year>/<int:month>/<int:day>/<slug:post>/', views.post_detail, name='post_detail'),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path(
        '<int:post_id>/comment/', views.post_comment, name='post_comment'
    ),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', views.post_search, name='post_search'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]