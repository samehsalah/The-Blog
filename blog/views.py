from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.http import Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.core.mail import send_mail
from django.views.decorators.http import require_POST
from taggit.models import Tag
from django.db.models import Count

# Create your views here.
def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    # Pagination with 3 posts per page
    paginator = Paginator(post_list, 3)
    #If the page parameter is not in the GET parameters of the request, we use the default value 1 to load the first page of results.
    page_number = request.GET.get('page')
    try:
        posts = paginator.page(page_number)
    except EmptyPage:
        # If page_number is out of range deliver last page of results
        posts = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        posts = paginator.page(1)
    #pass the page number and the posts object to the template.
    return render(request,'blog/post/list.html', {'posts':posts, 'tag':tag})

#Another way to develope view is by using Class instead of function, 
#in the following we will develop class equivalent to post_list.
class PostListView(ListView):
    """
    Alternative post list view
    """
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    #If you don’t set a default template, ListView will use blog/post_list.html by default.
    #Django’s ListView generic view passes the page requested in a variable called page_obj
    template_name = 'blog/post/list.html'

        
def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                            status=Post.Status.PUBLISHED,
                            publish__year=year,
                            publish__month=month,
                            publish__day=day,
                            slug=post,)
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    # Form for user to comment
    form = CommentForm()
    # List of similar posts
    post_tags_id = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_id).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]

    return render(request,'blog/post/detail.html',{'post': post, 'comments':comments, 'form':form, 'similar_posts':similar_posts})


# this function is for handling post form and send email with recommendations. 
def post_share(request, post_id):
    # Retrive post by id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED) 
    #   The HTTP request method allows us to differentiate whether the form is being submitted. A GET request will
        #indicate that an empty form has to be displayed to the user and a POST request will indicate the form
        #is being submitted.
    sent = False
    if request.method == 'POST':
         form = EmailPostForm(request.POST)
         if form.is_valid():
            #If any field contains invalid data, then is_valid() returns False. The list of validation errors
            #can be obtained with form.errors
            # If your form data does not validate, cleaned_data will contain only the valid fields.
             cd = form.cleaned_data
             #We use this path as an input for request.build_absolute_uri() to
             #build a complete URL, including the HTTP schema and hostname.
             post_url = request.build_absolute_uri(
             post.get_absolute_url())
             subject = f"{cd['name']} recommends you read " \
                       f"{post.title}"
             message = f"Read {post.title} at {post_url}\n\n" \
                       f"{cd['name']}\'s comments: {cd['comments']}"
             send_mail(subject, message, 'samehukstiriling@gmail.com',
                      [cd['to']])
             sent = True

    else: 
        form = EmailPostForm()
    return render(request, 'blog/post/share.html',{'post':post, 'form':form, 'sent':sent})
            
            
@require_POST
def post_comment(request,post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    # A comment was post
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Create comment object without saving in the database
        comment = form.save(commit=False)
        # assing the post to the commnet
        comment.post = post
        # Save the comment in the database
        #The save() method is available for ModelForm but not for Form instances since they are not linked to any model.
        comment.save()
    return render (request, 'blog/post/comment.html', {'post':post, 'form':form, 'comment':comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            
            search_vector = SearchVector('title',weight='A') + SearchVector('body', weight='B')
            #Django provides a SearchQuery class to translate terms into a search query object. By default, the
            #terms are passed through stemming algorithms, which helps you to obtain better matches.
            search_query = SearchQuery(query) # For stemming and removing stop words.
            results = Post.published.annotate(search=search_vector, rank=SearchRank(search_vector,search_query)
                                              ).filter(rank__gte=0.3).order_by('-rank')
            
    return render(request,
            'blog/post/search.html',
            {'form': form,
            'query': query,
            'results': results})