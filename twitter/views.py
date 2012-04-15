# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect
from twitter.models import *
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
import datetime, re

from urllib import urlencode

# Create your views here.

TWEETS_EN_PAGE = 5
TWEETS_EN_PROFILE = 5

def borrar(request, tweet_id):
	t = get_object_or_404(Tweet, id = tweet_id)
	if t.user == request.user: #El usuario actual es el propietario del tweeet
		t.activo = False
		t.save()
	return HttpResponseRedirect('/twitter/')

def buscar(request, page = 1):
	if page < 2:
		page = 1
	if request.GET.has_key('busqueda'):
		n = TWEETS_EN_PAGE * (int(page) - 1)
		t = Tweet.objects.filter(contenido__icontains = request.GET['busqueda']).order_by('-fecha')[n:n + TWEETS_EN_PAGE]
		return render_to_response('twitter/index.html',
		{
			'logueado' : request.user,
			'next' : int(page) + 1,
			'page' : page,
			'prev' : int(page) - 1,
			'tweets' : t,
			'page_prefix' : 'buscar/',
			'page_sufix' : '?%s' % urlencode({'busqueda' : request.GET['busqueda']}),
			'busqueda' : request.GET['busqueda'],
			'ntweets' : len(Tweet.objects.filter(user = request.user)),
			'u_seguidores' : len(Follow.objects.filter(activo = True,
				follower = Profile.objects.get(user = request.user))),
			'u_siguiendo' : len(Follow.objects.filter(activo = True,
				followed = request.user)),
		}, RequestContext(request))
	else:
		return HttpResponseRedirect('/twitter/')

def conf(request):
	u = request.user
	p = get_object_or_404(Profile, user = u)
	try:
		if not u.check_password(request.POST['oldpass']):
			return render_to_response('twitter/conf.html',{
				'mensaje' : '<h3>Introduzca su contraseña actual correctamente</h3>',
				'nombre' : u.first_name,
				'apellido' : u.last_name,
				'email' : u.email,
				'ubicacion' : p.ubicacion,
				'bio' : p.frase,
				'logueado' : request.user,
				'ntweets' : len(Tweet.objects.filter(user = request.user)),
				'u_seguidores' : len(Follow.objects.filter(activo = True,
					follower = Profile.objects.get(user = request.user))),
				'u_siguiendo' : len(Follow.objects.filter(activo = True,
					followed = request.user)),
				}, RequestContext(request))
		if request.POST['procesa'] == 'profile':
			u.first_name = request.POST['firstname']
			u.last_name = request.POST['lastname']
			u.email = request.POST['email']
			u.save()

			p.ubicacion = request.POST['ubicacion']
			p.frase = request.POST['bio']
			p.save()
		elif request.POST['procesa'] == 'pass':
			if request.POST['pass'] == request.POST['pass2']:
				u.set_password(request.POST['pass'])
				u.save()
				logout(request)
				return HttpResponseRedirect('/twitter/')
			else:
				return render_to_response('twitter/conf.html',{
					'mensaje' : 'Las contraseñas no coinciden',
					'nombre' : u.first_name,
					'apellido' : u.last_name,
					'email' : u.email,
					'ubicacion' : p.ubicacion,
					'bio' : p.frase,
					'logueado' : request.user,
					'ntweets' : len(Tweet.objects.filter(user = request.user)),
					'u_seguidores' : len(Follow.objects.filter(activo = True,
						follower = Profile.objects.get(user = request.user))),
					'u_siguiendo' : len(Follow.objects.filter(activo = True,
						followed = request.user)),
					}, RequestContext(request))
		return HttpResponseRedirect('/twitter/configuracion/')
	except KeyError:
		return render_to_response('twitter/conf.html',{
			'nombre' : u.first_name,
			'apellido' : u.last_name,
			'email' : u.email,
			'ubicacion' : p.ubicacion,
			'bio' : p.frase,
			'logueado' : request.user,
			'ntweets' : len(Tweet.objects.filter(user = request.user)),
			'u_seguidores' : len(Follow.objects.filter(activo = True,
				follower = Profile.objects.get(user = request.user))),
			'u_siguiendo' : len(Follow.objects.filter(activo = True,
				followed = request.user)),
			}, RequestContext(request))

def conversacion(request, conversacion, page = 1):
	if page < 2:
		page = 1
	n = TWEETS_EN_PAGE * (int(page) - 1)
	tweets = []
	t = get_object_or_404(Tweet, pk = conversacion)
	tweets.append(t)
	while t.respuesta: #Mientras este contestando a otro tweet
		t = get_object_or_404(Tweet, pk = int(t.respuesta))
		tweets.append(t)
	return render_to_response('twitter/index.html',
	{
		'logueado' : request.user,
		'next' : int(page) + 1,
		'page' : page,
		'prev' : int(page) - 1,
		'tweets' : tweets,
		'page_prefix' : 'conversacion/%s/' % conversacion,
		'ntweets' : len(Tweet.objects.filter(user = request.user)),
		'u_siguiendo' : len(Follow.objects.filter(activo = True,
			follower = Profile.objects.get(user = request.user))),
		'u_seguidores' : len(Follow.objects.filter(activo = True,
			followed = request.user)),
	}, RequestContext(request))

def follow(request):
	try:
		user = request.POST['user']
	except KeyError:
		return HttpResponseRedirect('/twitter/')
	
	u = get_object_or_404(User, username = user)
	f = Follow.objects.filter(follower__user =request.user, followed = u)
	if f: #Ya hay algun follow del mismo usuario, se cambia el activo en vez de crear uno nuevo
		f = f[0]
		f.activo = not f.activo #Si lo esta siguiendo lo deja de seguir, sino lo sigue
		f.save()
	else: #Crea un nuevo objecto folllow
		f = Follow.objects.create(
			fecha = datetime.datetime.now(),
			activo = True,
			follower = Profile.objects.get(user = request.user),
			followed = u
		)
		f.save()
	return HttpResponseRedirect('/twitter/profile/%s/' % user)

def index(request, page = 1):
	if page < 2:
		page = 1
	n = TWEETS_EN_PAGE * (int(page) - 1)
	if request.user.is_authenticated():
		#t = Tweet.objects.all().order_by('-fecha')[n:n + TWEETS_EN_PAGE]
		p = Profile.objects.get(user = request.user)
		users = Follow.objects.filter(follower = p, activo = True) #Busca los users que sigue el usuario
		users = [u.followed for u in users] #Hace que users sea un array de los usuarios que sigue
		users.append(request.user) #Le agrega el usuario actual
		tweets_ = Tweet.objects.filter(user__in = users, activo = True).order_by('-fecha')[n:n + TWEETS_EN_PAGE]

		#Procesa retweets
		tweets = []
		for t in tweets_:
			if t.retweet == True:
				rt = Tweet.objects.get(pk = int(t.contenido))
				rt.retwitteado = 1
				rt.retweetter = t.user
				rt.rt_id = t.id
				tweets.append(rt)
			else:
				tweets.append(t)

		return render_to_response('twitter/index.html',
		{
			'logueado' : request.user,
			'next' : int(page) + 1,
			'page' : page,
			'prev' : int(page) - 1,
			'tweets' : tweets,
			'ntweets' : len(Tweet.objects.filter(user = request.user)),
			'u_siguiendo' : len(Follow.objects.filter(activo = True,
				follower = Profile.objects.get(user = request.user))),
			'u_seguidores' : len(Follow.objects.filter(activo = True,
				followed = request.user)),
		}, RequestContext(request))
	else:
		return HttpResponseRedirect('/twitter/login/')
		
def login_process(request):
	try:
		user = authenticate(username = request.POST['user'],
			password = request.POST['pass'])
	except KeyError:
		return render_to_response('twitter/login.html',{
			'mensaje_login' : 'Rellene todos los campos',
			},RequestContext(request)) 
	if user is not None:
		#User y pass correctos
		if user.is_active:
			login(request, user)
		else:
			return render_to_response('twitter/login.html',{
				'mensaje_login' : 'El usuario ha sido eliminado',
			},RequestContext(request))
	else:
		return render_to_response('twitter/login.html',{
			'mensaje_login' : 'Ingrese el usuario y clave correctamente',
		},RequestContext(request))
	return HttpResponseRedirect('/twitter/')

def profile(request, username, page = 1):
	if page < 2:
		page = 1
	n = TWEETS_EN_PROFILE * (int(page) - 1)
	u = get_object_or_404(User, username=username)
	#tweets = Tweet.objects.filter(user = u).order_by('-fecha')
	tweets_ = u.tweet_set.all().filter(activo = True).order_by('-fecha')

	#Procesa retweets
	tweets = []
	for t in tweets_:
		if t.retweet == True:
			rt = Tweet.objects.get(pk = int(t.contenido))
			rt.retwitteado = 1
			rt.retweetter = t.user
			rt.rt_id = t.id
			tweets.append(rt)
		else:
			tweets.append(t)

	p = Profile.objects.get(user = request.user) #El perfil del usuario
	f = Follow.objects.filter(follower = p, activo = True) #Los objetos follow activos
	f = [user.followed for user in f] #Convierte f a un array de usuarios que sigue

	return render_to_response('twitter/profile.html',
	{
		'following' : (u in f),
		'length' : len(tweets),
		'logueado' : request.user,
		'next' : int(page) + 1,
		'page' : page,
		'prev' : int(page) - 1,
		'profile' : get_object_or_404(Profile, user=u),
		'tweets' : tweets[n:n + TWEETS_EN_PROFILE],
		'user' : u,
		'siguiendo' : f,
		'seguidores' : Follow.objects.filter(activo = True, followed = u),
		'ntweets' : len(Tweet.objects.filter(user = request.user)),
		'u_siguiendo' : len(Follow.objects.filter(activo = True,
			follower = Profile.objects.get(user = request.user))),
		'u_seguidores' : len(Follow.objects.filter(activo = True,
			followed = request.user)),
	}, RequestContext(request))

def register(request):
	try:
		request.POST['procesa']
		try:
			if not re.match('^[a-zA-Z0-9_]+$', request.POST['user']):
				return render_to_response(
					'twitter/login.html',
					{'mensaje_register' : 'El nombre de usuario solo puede contener letras, numeros y _'},
					RequestContext(request))
			if not re.match('^[^@]+@[^@]+$', request.POST['email']):
				return render_to_response(
					'twitter/login.html',
					{'mensaje_register' : 'Ingrese un email valido'},
					RequestContext(request))
			if request.POST['pass'] != request.POST['pass2']:
				return render_to_response(
					'twitter/login.html',
					{'mensaje_register' : 'No coincide el password'},
					RequestContext(request))
			if User.objects.filter(username = request.POST['user']):
				return render_to_response(
					'twitter/login.html',
					{'mensaje_register' : 'El usuario ya existe'},
					RequestContext(request))
			u = User.objects.create_user(
				request.POST['user'],
				request.POST['email'],
				request.POST['pass'],
			)
			u.first_name = request.POST['firstname']
			u.last_name = request.POST['lastname']

			#Comprueba que existan las otras claver
			request.POST['ubicacion']
			request.POST['bio']

			u.save()

			p = Profile.objects.create(
				user = u,
				frase = request.POST['bio'],
				ubicacion = request.POST['ubicacion'],
				avatar = ''
			)
			p.save()
			return HttpResponseRedirect('/twitter/')
		except KeyError:
			return render_to_response('twitter/login.html',
				{'message' : 'Rellene todos los campos'},
				RequestContext(request))
	except KeyError:
		return render_to_response('twitter/login.html', {}, RequestContext(request))

def responder(request, tweet_id):
	return render_to_response('twitter/responder.html',
	{
		'logueado' : request.user,
		'tweet' : get_object_or_404(Tweet, pk = tweet_id), 
		'ntweets' : len(Tweet.objects.filter(user = request.user)),
		'u_siguiendo' : len(Follow.objects.filter(activo = True,
			follower = Profile.objects.get(user = request.user))),
		'u_seguidores' : len(Follow.objects.filter(activo = True,
			followed = request.user)),
	}, RequestContext(request))

def retweet(request, tweet_id):
	if request.POST.has_key('confirma'):
		#Procesa
		t = Tweet.objects.create(
			user = request.user,
			fecha = datetime.datetime.now(),
			contenido = str(tweet_id),
			retweet = True #Indica que es retweet, el contenido es el id del tweet original
		)
		t.save()
		return HttpResponseRedirect('/twitter/')
	else:
		return render_to_response('twitter/retweet.html',
		{
			'logueado' : request.user,
			'tweet' : get_object_or_404(Tweet, id = tweet_id),
			'ntweets' : len(Tweet.objects.filter(user = request.user)),
			'u_siguiendo' : len(Follow.objects.filter(activo = True,
				follower = Profile.objects.get(user = request.user))),
			'u_seguidores' : len(Follow.objects.filter(activo = True,
				followed = request.user)),
		}, RequestContext(request))

def seguidores(request, method, username):
	u = get_object_or_404(User, username = username)
	p = get_object_or_404(Profile, user__username = username)
	if method == 'seguidores':
		u = Follow.objects.filter(followed = u, activo = True).order_by('-fecha')
		u = [f.follower.user for f in u]
	elif method == 'siguiendo':
		u = Follow.objects.filter(follower = p, activo = True).order_by('-fecha')
		u = [f.followed for f in u]
	
	for n in range(len(u)):
		u[n].profile = get_object_or_404(Profile, user = u[n])

	return render_to_response(
	'twitter/seguidores.html',
	{
		'logueado' : request.user,
		'users' : u,
		'ntweets' : len(Tweet.objects.filter(user = request.user)),
		'u_siguiendo' : len(Follow.objects.filter(activo = True,
			follower = Profile.objects.get(user = request.user))),
		'u_seguidores' : len(Follow.objects.filter(activo = True,
			followed = request.user)),
	}, RequestContext(request))

def tweet(request):
	try:
		content = request.POST['content']
	except KeyError:
		return HttpResponseRedirect('/twitter/')
	try:
		respuesta = int(request.POST['respuesta'])
	except (KeyError, ValueError):
		respuesta = None
	
	if respuesta is None:
		t = Tweet.objects.create(
			user = request.user,
			fecha = datetime.datetime.now(),
			contenido = content,
		)
	else:
		t = Tweet.objects.create(
			user = request.user,
			fecha = datetime.datetime.now(),
			contenido = content,
			respuesta = respuesta,
		)
	t.save()
	return HttpResponseRedirect('/twitter/')

def twitter_login(request):
	return render_to_response('twitter/login.html',
		{},
		RequestContext(request))

def twitter_logout(request):
	logout(request)
	return HttpResponseRedirect('/twitter/')
