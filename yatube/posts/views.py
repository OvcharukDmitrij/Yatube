from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm

NUMBER_OF_POSTS = 10  # количество отображаемых постов на странице


def paginat(request, queryset):
    pagin = Paginator(queryset, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    return pagin.get_page(page_number)


def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': paginat(request, post_list),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': paginat(request, group_list),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all().filter(author__username=username)
    num_of_posts = posts.count()
    users = User.objects.all()
    user = request.user
    following = False
    if user in users:
        if user.follower.filter(author_id=author.id):
            following = True
    context = {
        'num_of_posts': num_of_posts,
        'author': author,
        'page_obj': paginat(request, posts),
        'following': following,
        'users': users
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    num_of_posts = Post.objects.filter(author=post.author).count()
    context = {
        'post': post,
        'num_of_posts': num_of_posts,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
        'is_edit': False
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    authors = user.follower.values_list('author')
    posts = Post.objects.filter(author__in=authors)
    context = {
        'page_obj': paginat(request, posts),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    user = request.user
    if user == author or user.follower.filter(author=author):
        return redirect('posts:profile', username=username)
    Follow.objects.create(
        user_id=user.id,
        author_id=author.id,
    )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = User.objects.get(username=username)
    follow_author = Follow.objects.get(author_id=author.id)
    follow_author.delete()

    return redirect('posts:profile', username=username)
