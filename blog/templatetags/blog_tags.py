from django import template
from ..models import Post
from django.db.models import Count
import markdown
from django.utils.safestring import mark_safe
# Each module that contains template tags needs to define a variable called register to be a valid tag library.
register = template.Library()

@register.simple_tag
def total_posts():
    return Post.published.count()

@register.inclusion_tag('blog/post/latest_posts.html')
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}

@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(
            total_comments=Count('comments')
                ).order_by('-total_comments')[:count]
    
    
@register.filter(name='markdown')  # name indicate to name of the filter
def markdown_format(text):
    #We use the mark_safe function provided by Django to mark the result as safe HTML to be rendered
    #in the template. By default, Django will not trust any HTML code and will escape it before placing it
    #in the output. The only exceptions are variables that are marked as safe from escaping. This behavior
    #prevents Django from outputting potentially dangerous HTML and allows you to create exceptions
    #for returning safe HTML.
    return mark_safe(markdown.markdown(text))

