import re
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q   
from django.contrib.auth.models import User 
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message
from .forms import RoomForm, UserForm


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        #get username and password
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        #check to see if user exists
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
            
        #authenticate user if user exist
        user = authenticate(request, username=username, password=password)
        
        #creates a seesion once user is logged in
        if user is not None:
            login(request, user) 
            return redirect('home') #redirect to home page
        else:
            messages.error(request, 'Username or Password does not exist')
    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = UserCreationForm()
    #pass in user data
    if request.method == 'POST':
        #throw the value into the form variable
        form = UserCreationForm(request.POST)
        #check if form is valid
        if form.is_valid():
            user = form.save(commit=False)
            #get the username and ensure it is lower case
            user.username = user.username.lower()
            #save the user
            user.save()
            #log the user in
            login(request, user)
            #redirect the user
            return redirect('home')
        else:
            messages.error(request, 'An error occured during registration')
            
    return render(request, 'base/login_register.html', {'form': form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) 
    ) 
    
    topics = Topic.objects.all()[0:4]
    room_count = rooms.count() 
    #for creating the recent activties, displaying user, 
    # user reply and room 
    # room_messages= Message.objects.all()
    
    #make 'Recent Activity' specific to respective rooms
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    
    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count, 
               'room_messages':room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    #get all rooms
    room = Room.objects.get(id=pk)
    #querying the child object message from the parent object Room in lowercase
    #room.message
    room_messages = room.message_set.all()# _set.all() for a one-to-many relationship
    #display participant of a room
    participants = room.participants.all() #.all() cos it is a many-to-many relationship
    if request.method == 'POST':
        messages = Message.objects.create(
            user=request.user,
            room=room,
            #get the value of the message sent which is an html element with name 'body'
            body=request.POST.get('body')   
        )
        #adding a user as a participant of a room
        room.participants.add(request.user)
        #redirect user to the room after submitting
        return redirect('room', pk=room.id)
    context = {'room': room, 'room_messages': room_messages, 
               'participants':participants }
    return render(request, 'base/room.html', context)



def userProfile(request, pk):
    user = User.objects.get(id=pk)
    
    #get all users room
    #remember we can get all children of a specific Model/object  by
    #doing modelname_set and .all() means we getting all of them
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user':user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    
    #to display topics in the create room page dynamically
    topics = Topic.objects.all()
    
    #form variable to become an instance of the RoomForm
    form = RoomForm()
    #check to see if the method is post
    if request.method == 'POST':
    #add the data to the form
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host=request.user,
            topic=topic,
            name= request.POST.get('name'),
            description= request.POST.get('description'),
        )
        
        # form = RoomForm(request.POST)
        #check to see if form is valid
        # if form.is_valid():
            #we havent gotten the room host yet so we set commit to false &
            #get the room value 
            # room = form.save(commit=False)
            #set the room host to the user
            # room.host = request.user
            #now we save permanent
            # room.save()
            
            #redirect user to home page
        return redirect('home')
    context = {'form': form, 'topics' : topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    #to display topics in the update room page dynamically
    topics = Topic.objects.all()
    #get the room
    room = Room.objects.get(id=pk)
    #get the form
    form = RoomForm(instance=room)
    
    #ensure only owner of room can update a room
    if request.user != room.host:
        return HttpResponse("You are not allowed here!!")
    
    if request.method == 'POST':
        
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        
        # form = RoomForm(request.POST, instance=room)
        # if form.is_valid:
        #     form.save()
        return redirect('home')
    context = {'form': form, 'topics': topics, 'room':room}
    return render(request, 'base/room_form.html', context)
 

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    #ensure only owner of room can delete
    if request.user != room.host:
        return HttpResponse("You are not allowed here!!")
    
    if request.method == "POST":
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj':room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    #ensure only owner of room can delete
    if request.user != message.user:
        return HttpResponse("You are not allowed here!!")
    
    if request.method == "POST":
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj':message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
    return render(request, 'base/update-user.html', {'form':form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    
    topics = Topic.objects.filter(name__icontains=q)
    
    return render (request, 'base/topics.html', {'topics': topics})
    
    

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})