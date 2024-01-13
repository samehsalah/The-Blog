from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse  #to build URLs dynamically using their name and any required parameters.
from taggit.managers import TaggableManager

""" The default manager for every model is the objects manager. This manager retrieves all the objects
in the database. However, we can define custom managers for models.
Let’s create a custom manager to retrieve all posts that have a PUBLISHED status
Note: The first manager declared in a model becomes the default manager."""
class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)

class Post(models.Model):
    
    class Status (models.TextChoices):
        DRAFT = 'DF','Draft'
        PUBLISHED = 'PB','Published'
        
    title = models.CharField(max_length=250)
    publish = models.DateTimeField(default=timezone.now)
    """The 'unique_for_date' constraint ensures that the slug field is unique for the date stored in the publish field.
        thus, We can now retrieve single posts by the publish and slug fields."""
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated  = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=2, choices=Status.choices, default=Status.DRAFT)
    objects = models.Manager() # The default manager.
    published = PublishedManager() # Our custom manager.
    tags = TaggableManager()  # The tags manager will allow you to add, retrieve, and remove tags from Post objects.
    
    
    '''We indicate descending order by using a hyphen before the field name, -publish. Posts will be returned in reverse
        chronological order by default.'''
    class Meta:
        ordering = ['-publish']
        '''Index ordering is not supported on MySQL. If you use MySQL for the database, a descending
            index will be created as a normal index.'''
        indexes = [
            models.Index(fields=['-publish'])
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url (self):
        """We have used the blog namespace followed by a colon and the URL name post_detail. 
        Remember that the blog namespace is defined in the main urls.py file of the project when including the URL patterns
        from blog.urls, we will send this to the template"""
        return reverse('blog:post_detail',args=[self.publish.year,
                                                self.publish.month,
                                                self.publish.day,
                                                self.slug])
        
        
class Comment(models.Model):
    #If you don’t define the related_name attribute, Django will use the name of the model in lowercase, followed by _set
    #(that is, comment_set) to name the relationship of the related object to the object of the model, where
    #this relationship has been defined.
    
    #We can retrieve the post of a comment object using comment.post and
    #retrieve all comments associated with a post object using post.comments.all().
    name = models.CharField(max_length=80)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments') 
    email = models.EmailField()
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['created']
        indexes = [
            models.Index(fields=['created'])
        ]
        
    def __str__(self):
        return f"comment by {self.name} on {self.post}"