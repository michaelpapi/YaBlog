from django.views.generic import ListView
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from taggit.models import Tag
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Count
from django.core.mail import EmailMessage
from decouple import config

from .models import Post, Comment
from .forms import CommentForm, EmailPostForm, SearchForm

# Create your views here.

def index(request):
    """Home page for yablog"""
    if request.user.is_authenticated:
        return redirect('blog:post_list')
    return render(request, 'blog/index.html')


class PostListView(LoginRequiredMixin, ListView):
    """
    Alternate post list view
    """
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'

    def get_queryset(self):
        queryset = Post.published.all()
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags__in=[tag])
        return queryset
    
    def get_context_data(self, **kwargs):
        # Add the 'tag' to the context if filtering by tag
        context = super().get_context_data(**kwargs)
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            context['tag'] = get_object_or_404(Tag, slug=tag_slug)
        return context

@login_required
def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        status=Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day
    )
    # Displaying a list of active comments for the post
    comments = post.comments.filter(active=True)
    # Form for users to comment
    form = CommentForm()

     # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(
        tags__in=post_tags_ids
    ).exclude(id=post.id)
    similar_posts = similar_posts.annotate(
        same_tags=Count('tags')
    ).order_by('-same_tags', '-publish')[:4]

    return render(
        request, 'blog/post/detail.html', {'post': post, 'comments': comments, 'form': form, 'similar_posts': similar_posts}
    )

@login_required
def post_share(request, post_id):
    # Retrive the post by it's id
    post = get_object_or_404(
        Post,
        id=post_id,
        status = Post.Status.PUBLISHED
    )
    sent = False

    if request.method == 'POST':
        # Form has been submitted.
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields all passed validation
            cd = form.cleaned_data
            # Uses the logged-in user's email instead of form input
            user_email = request.user.email
            # sends the email
            post_url = request.build_absolute_uri(
                post.get_absolute_url()
            )
            subject = (
                f"{cd['name']} ({user_email}) recommends you read {post.title}"
            )
            message = (
                f"Read {post.title} at {post_url} \n\n"
                f"{cd['name']}\'s comments: {cd['comments']}"
            )
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=config('EMAIL_HOST_USER'),
                to=[cd['to']],
                headers={'Reply-To': user_email},
            )
            email.send()
            sent = True

    else:
        form = EmailPostForm()
    return render(
        request,
        'blog/post/share.html',
        {
            'post': post,
            'form': form,
            'sent': sent,
        }
    )


@require_POST 
@login_required
def post_comment(request, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        status=Post.Status.PUBLISHED
    )

    comment = None
    # A comment was posted
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Creates a Comment object without saving yet
        comment = form.save(commit=False)
        # Assign the comment to the comment
        comment.post = post
        # Assign with logged-in user
        comment.user = request.user
        # Assign email from logged in user
        comment.email = request.user.email
        # Save the comment to the database
        comment.save()
    return render(
        request,
        'blog/post/comment.html',
        {
            'post': post,
            'form': form,
            'comment' : comment,
        }
    )


@login_required
def post_search(request):
    form = SearchForm()
    query = None
    results = []

    # When a query/search item is submitted.
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = (
                Post.published.annotate(
                    similarity=TrigramSimilarity('title', query),
                )
                .filter(similarity__gt=0.1)
                .order_by('similarity')
            )

    return render(
        request,
        'blog/post/search.html',
        {
            'form': form,
            'query': query,
            'results': results,
        }
    )


@login_required
def delete_comment(request, comment_id):
    # Gets comment, and ensures that user owns it. 
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    if request.method == 'POST':
        comment.delete()
        # Redirects back to post after deleting.
        return redirect('blog:post_detail', year=comment.post.publish.year, month=comment.post.publish.month, day=comment.post.publish.day, post=comment.post.slug)